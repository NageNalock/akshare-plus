import { startTransition, useDeferredValue, useEffect, useState } from "react";

import CataloguePane from "./components/CataloguePane";
import FunctionWorkbench from "./components/FunctionWorkbench";
import ResultPanel from "./components/ResultPanel";

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "string"
        ? payload
        : payload.detail || JSON.stringify(payload, null, 2);
    throw new Error(message);
  }
  return payload;
}

function getInitialFieldState(parameter) {
  let value = "";

  if (parameter.choices?.length) {
    value = parameter.default ?? parameter.choices[0] ?? "";
  } else if (parameter.kind === "boolean") {
    value = parameter.default ?? true;
  } else if (parameter.kind === "json") {
    value =
      parameter.default !== null && parameter.default !== undefined
        ? JSON.stringify(parameter.default, null, 2)
        : "";
  } else {
    value =
      parameter.default !== null && parameter.default !== undefined
        ? String(parameter.default)
        : "";
  }

  return {
    useDefault: Boolean(parameter.has_default),
    value,
  };
}

function buildInitialFormState(detail) {
  const nextState = {};
  for (const parameter of detail.parameters || []) {
    nextState[parameter.name] = getInitialFieldState(parameter);
  }
  return nextState;
}

function isEmptyValue(value) {
  return value === "" || value === null || value === undefined;
}

function buildExecutionPayload(detail, formState, previewRows) {
  const parameters = {};

  for (const parameter of detail.parameters || []) {
    const fieldState = formState[parameter.name] || getInitialFieldState(parameter);

    if (fieldState.useDefault) {
      continue;
    }

    const value = fieldState.value;
    if (parameter.required && isEmptyValue(value)) {
      throw new Error(`参数 ${parameter.name} 为必填项`);
    }

    if (!parameter.required && !parameter.has_default && isEmptyValue(value)) {
      continue;
    }

    parameters[parameter.name] = value;
  }

  return {
    preview_rows: Number(previewRows || 100),
    parameters,
  };
}

function getCategoryLabel(categories, activeCategory) {
  if (!activeCategory) {
    return "全部分类";
  }
  return categories.find((item) => item.name === activeCategory)?.name || activeCategory;
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [catalogue, setCatalogue] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedName, setSelectedName] = useState("");
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [detailCache, setDetailCache] = useState({});
  const [searchValue, setSearchValue] = useState("");
  const [activeCategory, setActiveCategory] = useState("");
  const [formState, setFormState] = useState({});
  const [previewRows, setPreviewRows] = useState(100);
  const [resultPayload, setResultPayload] = useState(null);
  const [resultError, setResultError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const deferredSearch = useDeferredValue(searchValue);

  const filteredItems = catalogue.filter((item) => {
    if (activeCategory && item.category !== activeCategory) {
      return false;
    }

    if (!deferredSearch.trim()) {
      return true;
    }

    const haystack = [
      item.name,
      item.title,
      item.category,
      item.module,
      item.description || "",
      item.section || "",
    ]
      .join(" ")
      .toLowerCase();

    return haystack.includes(deferredSearch.trim().toLowerCase());
  });

  const selectedCatalogueItem =
    catalogue.find((item) => item.name === selectedName) || filteredItems[0] || null;
  const topCategories = categories
    .slice()
    .sort((left, right) => right.count - left.count)
    .slice(0, 8);
  const activeCategoryLabel = getCategoryLabel(categories, activeCategory);
  const requiredParameterCount = selectedDetail?.parameters?.filter((item) => item.required).length || 0;

  useEffect(() => {
    let disposed = false;

    async function boot() {
      setLoading(true);
      setStatusMessage("正在加载 AKShare 函数目录...");

      try {
        const [healthPayload, functionsPayload] = await Promise.all([
          requestJson("/api/health"),
          requestJson("/api/functions"),
        ]);

        if (disposed) {
          return;
        }

        setHealth(healthPayload);
        setCatalogue(functionsPayload.items || []);
        setCategories(functionsPayload.categories || []);
        setStatusMessage(
          healthPayload.ready
            ? "服务已就绪，函数目录、HTTP 执行和 MCP 接入都可以直接使用。"
            : healthPayload.error || "AKShare 当前还没有准备完成。",
        );

        const hashName = decodeURIComponent(window.location.hash.replace(/^#/, ""));
        const nextSelection = hashName || functionsPayload.items?.[0]?.name || "";
        if (nextSelection) {
          setSelectedName(nextSelection);
        }
      } catch (error) {
        if (!disposed) {
          setStatusMessage(error.message || String(error));
        }
      } finally {
        if (!disposed) {
          setLoading(false);
        }
      }
    }

    boot();

    function onHashChange() {
      const hashName = decodeURIComponent(window.location.hash.replace(/^#/, ""));
      if (hashName) {
        startTransition(() => setSelectedName(hashName));
      }
    }

    window.addEventListener("hashchange", onHashChange);
    return () => {
      disposed = true;
      window.removeEventListener("hashchange", onHashChange);
    };
  }, []);

  useEffect(() => {
    if (!selectedDetail?.name) {
      document.title = "AKShare Dashboard";
      return;
    }

    document.title = `${selectedDetail.name} · AKShare Dashboard`;
  }, [selectedDetail]);

  useEffect(() => {
    let disposed = false;
    if (!selectedName) {
      return undefined;
    }

    async function loadDetail() {
      setDetailLoading(true);
      setResultPayload(null);
      setResultError("");

      if (detailCache[selectedName]) {
        const cached = detailCache[selectedName];
        setSelectedDetail(cached);
        setFormState(buildInitialFormState(cached));
        setDetailLoading(false);
        return;
      }

      setSelectedDetail(null);
      setFormState({});

      try {
        const detail = await requestJson(`/api/functions/${encodeURIComponent(selectedName)}`);
        if (disposed) {
          return;
        }

        setDetailCache((current) => ({ ...current, [selectedName]: detail }));
        setSelectedDetail(detail);
        setFormState(buildInitialFormState(detail));
        window.location.hash = encodeURIComponent(selectedName);
      } catch (error) {
        if (!disposed) {
          setResultError(error.message || String(error));
        }
      } finally {
        if (!disposed) {
          setDetailLoading(false);
        }
      }
    }

    loadDetail();
    return () => {
      disposed = true;
    };
  }, [detailCache, selectedName]);

  function handleSelect(name) {
    startTransition(() => {
      setSelectedName(name);
    });
  }

  function handleFieldChange(name, value) {
    setFormState((current) => ({
      ...current,
      [name]: {
        ...(current[name] || {}),
        value,
      },
    }));
  }

  function handleUseDefaultChange(name, useDefault) {
    setFormState((current) => ({
      ...current,
      [name]: {
        ...(current[name] || {}),
        useDefault,
      },
    }));
  }

  function handleReset() {
    if (!selectedDetail) {
      return;
    }
    setFormState(buildInitialFormState(selectedDetail));
    setPreviewRows(100);
    setResultPayload(null);
    setResultError("");
  }

  function handleClearFilters() {
    setSearchValue("");
    setActiveCategory("");
  }

  async function handleExecute() {
    if (!selectedDetail) {
      return;
    }

    setSubmitting(true);
    setResultError("");
    setResultPayload(null);

    try {
      const payload = buildExecutionPayload(selectedDetail, formState, previewRows);
      const result = await requestJson(
        `/api/functions/${encodeURIComponent(selectedDetail.name)}/execute`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );
      setResultPayload(result);
      setStatusMessage(`函数 ${selectedDetail.name} 已成功执行。`);
    } catch (error) {
      setResultError(error.message || String(error));
      setStatusMessage(error.message || String(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />

      <header className="dashboard-hero frost-card">
        <div className="hero-copy">
          <p className="eyebrow">AKShare Dashboard</p>
          <h1>AKShare Dashboard</h1>
          <p className="banner-text">
            把 AKShare 的函数浏览、参数填写、HTTP 执行结果和 MCP 接入，收敛到一个更顺手的工作台里。
          </p>
          <div className="hero-action-row">
            <button className="primary-button" type="button" onClick={() => window.location.reload()}>
              刷新目录
            </button>
            <a className="ghost-button" href="#workspace">
              进入工作台
            </a>
          </div>
        </div>

        <div className="hero-side">
          <div className="status-shell prominent">
            <span className={`status-dot ${health?.ready ? "ok" : "warn"}`} />
            <div>
              <strong>{health?.ready ? "服务可用" : "服务检查中"}</strong>
              <p>{statusMessage || "准备中..."}</p>
            </div>
          </div>

          <div className="hero-metrics">
            <div className="metric-card">
              <span>函数总数</span>
              <strong>{health?.function_count ?? "-"}</strong>
            </div>
            <div className="metric-card">
              <span>分类数</span>
              <strong>{health?.category_count ?? "-"}</strong>
            </div>
            <div className="metric-card">
              <span>文档条目</span>
              <strong>{health?.docs_count ?? "-"}</strong>
            </div>
            <div className="metric-card">
              <span>MCP</span>
              <strong>{health?.mcp_ready ? "Enabled" : "Unavailable"}</strong>
            </div>
          </div>
        </div>
      </header>

      <section className="command-center frost-card">
        <div className="command-header">
          <div>
            <p className="eyebrow">Discovery</p>
            <h2>先筛选，再执行</h2>
            <p className="section-copy">
              搜索函数名、模块或说明，锁定分类后，右侧工作台会自动载入参数和集成信息。
            </p>
          </div>
          <div className="selection-card subtle-card">
            <span>当前选中</span>
            <strong>{selectedName || "未选择函数"}</strong>
            <small>
              {selectedDetail
                ? `${selectedDetail.parameters?.length || 0} 个参数 / ${requiredParameterCount} 个必填`
                : "从目录中选择一个函数开始"}
            </small>
          </div>
        </div>

        <div className="command-grid">
          <label className="field field-wide">
            <span>搜索函数</span>
            <input
              type="search"
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder="例如 stock_zh_a_hist / bond / macro / spot_price_qh"
            />
          </label>

          <label className="field">
            <span>分类</span>
            <select
              value={activeCategory}
              onChange={(event) => setActiveCategory(event.target.value)}
            >
              <option value="">全部分类</option>
              {categories.map((category) => (
                <option key={category.name} value={category.name}>
                  {category.name} ({category.count})
                </option>
              ))}
            </select>
          </label>

          <button
            className="ghost-button action-fit"
            type="button"
            onClick={handleClearFilters}
            disabled={!searchValue && !activeCategory}
          >
            清空筛选
          </button>
        </div>

        <div className="category-strip">
          <button
            type="button"
            className={`category-pill ${!activeCategory ? "active" : ""}`}
            onClick={() => setActiveCategory("")}
          >
            全部分类
          </button>
          {topCategories.map((category) => (
            <button
              key={category.name}
              type="button"
              className={`category-pill ${activeCategory === category.name ? "active" : ""}`}
              onClick={() => setActiveCategory(category.name)}
            >
              {category.name}
              <span>{category.count}</span>
            </button>
          ))}
        </div>

        <div className="command-footnote">
          <span>当前分类: {activeCategoryLabel}</span>
          <span>筛选结果: {filteredItems.length}</span>
          <span>目录状态: {health?.ready ? "已就绪" : "加载中"}</span>
        </div>
      </section>

      <div className="dashboard-layout">
        <CataloguePane
          filteredItems={filteredItems}
          selectedName={selectedName}
          selectedItem={selectedCatalogueItem}
          onSelect={handleSelect}
        />

        <main className="main-stage" id="workspace">
          {loading || detailLoading ? (
            <section className="frost-card loading-card">正在整理 AKShare 工作台...</section>
          ) : (
            <FunctionWorkbench
              detail={selectedDetail}
              formState={formState}
              previewRows={previewRows}
              submitting={submitting}
              onPreviewRowsChange={setPreviewRows}
              onFieldChange={handleFieldChange}
              onUseDefaultChange={handleUseDefaultChange}
              onReset={handleReset}
              onExecute={handleExecute}
              origin={window.location.origin}
              mcpPath={health?.mcp_path}
            />
          )}

          <ResultPanel
            resultPayload={resultPayload}
            error={resultError}
            selectedName={selectedName}
            selectedDetail={selectedDetail}
          />
        </main>
      </div>
    </div>
  );
}
