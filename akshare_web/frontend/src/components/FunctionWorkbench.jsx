import { useState } from "react";

function getFieldValue(field, parameter) {
  if (!field) {
    return parameter.kind === "boolean" ? true : "";
  }
  return field.value;
}

function shortenText(value, maxLength = 96) {
  if (!value) {
    return "";
  }

  const compactText = value.replace(/\s+/g, " ").trim();
  if (compactText.length <= maxLength) {
    return compactText;
  }
  return `${compactText.slice(0, maxLength).trimEnd()}...`;
}

function hasExpandableText(value, threshold = 96) {
  if (!value) {
    return false;
  }

  return value.length > threshold || value.includes("\n");
}

async function copyText(value) {
  if (
    !value
    || typeof navigator === "undefined"
    || !navigator.clipboard?.writeText
  ) {
    return false;
  }

  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}

function formatFieldRows(title, rows) {
  if (!rows?.length) {
    return "";
  }

  return [
    title,
    ...rows.map((row, index) => {
      const name = row.name || "-";
      const type = row.type || "-";
      const description = row.description || "-";
      return `${index + 1}. ${name} | ${type} | ${description}`;
    }),
  ].join("\n");
}

function buildDocumentationText(detail) {
  if (detail.documentation?.trim()) {
    return detail.documentation.trim();
  }

  const sections = [];

  if (detail.target_url) {
    sections.push(`目标地址: ${detail.target_url}`);
  }
  if (detail.description) {
    sections.push(`描述: ${detail.description}`);
  }
  if (detail.limit) {
    sections.push(`限量: ${detail.limit}`);
  }

  const inputSection = formatFieldRows("输入参数", detail.parameters);
  if (inputSection) {
    sections.push(inputSection);
  }

  const outputSection = formatFieldRows("输出参数", detail.output_parameters);
  if (outputSection) {
    sections.push(outputSection);
  }

  return sections.join("\n\n") || "暂无接口文档内容。";
}

function FieldControl({ parameter, fieldState, onFieldChange }) {
  const value = getFieldValue(fieldState, parameter);

  if (parameter.choices?.length) {
    return (
      <select
        value={String(value ?? "")}
        onChange={(event) => onFieldChange(parameter.name, event.target.value)}
      >
        {parameter.choices.map((choice) => (
          <option key={String(choice)} value={String(choice)}>
            {String(choice)}
          </option>
        ))}
      </select>
    );
  }

  if (parameter.kind === "boolean") {
    return (
      <div className="segmented-control">
        {[true, false].map((choice) => (
          <button
            key={String(choice)}
            type="button"
            className={value === choice ? "active" : ""}
            onClick={() => onFieldChange(parameter.name, choice)}
          >
            {String(choice)}
          </button>
        ))}
      </div>
    );
  }

  if (parameter.kind === "json") {
    return (
      <textarea
        value={String(value ?? "")}
        onChange={(event) => onFieldChange(parameter.name, event.target.value)}
        placeholder='{"symbol": "000001"}'
      />
    );
  }

  return (
    <input
      type={parameter.kind === "integer" || parameter.kind === "number" ? "number" : "text"}
      step={parameter.kind === "number" ? "any" : undefined}
      value={String(value ?? "")}
      onChange={(event) => onFieldChange(parameter.name, event.target.value)}
      placeholder={parameter.annotation || parameter.doc_type || parameter.kind}
    />
  );
}

function OutputSchema({ outputParameters }) {
  if (!outputParameters?.length) {
    return <p className="section-note">当前函数没有解析到输出字段说明。</p>;
  }

  return (
    <div className="table-shell">
      <table className="data-table compact">
        <thead>
          <tr>
            <th>字段</th>
            <th>类型</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {outputParameters.map((row, index) => (
            <tr key={`${row.name}-${index}`}>
              <td>{row.name || "-"}</td>
              <td>{row.type || "-"}</td>
              <td>{row.description || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LongTextCard({
  label,
  value,
  href,
  mono = false,
  emptyText = "未提供",
}) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const hasValue = Boolean(value);
  const displayValue = hasValue ? value : emptyText;
  const canExpand = hasValue && hasExpandableText(value);
  const previewText = shortenText(displayValue);

  async function handleCopy() {
    if (!hasValue) {
      return;
    }

    const copiedNow = await copyText(value);
    if (copiedNow) {
      setCopied(true);
      globalThis.setTimeout(() => setCopied(false), 1200);
    }
  }

  return (
    <div className="summary-card subtle-card long-value-card">
      <div className="long-value-head">
        <span>{label}</span>
        <div className="inline-actions">
          {href ? (
            <a href={href} target="_blank" rel="noreferrer" className="inline-link-button">
              打开
            </a>
          ) : null}
          {hasValue ? (
            <button className="text-button" type="button" onClick={handleCopy}>
              {copied ? "已复制" : "复制"}
            </button>
          ) : null}
          {canExpand ? (
            <button className="text-button" type="button" onClick={() => setExpanded((current) => !current)}>
              {expanded ? "收起" : "展开"}
            </button>
          ) : null}
        </div>
      </div>

      <div className={`long-value-preview ${mono ? "mono" : ""}`}>{previewText}</div>

      {expanded && hasValue ? (
        <div className={`long-value-full ${mono ? "mono" : ""}`}>{value}</div>
      ) : null}
    </div>
  );
}

function DocumentationPanel({ detail }) {
  const [expanded, setExpanded] = useState(false);

  const documentationText = buildDocumentationText(detail);
  const canCollapse =
    documentationText.length > 420 || documentationText.split("\n").length > 14;

  return (
    <section className="frost-card documentation-panel">
      <div className="section-header section-header-split">
        <div>
          <h3>接口文档</h3>
          <p>直接展示当前接口对应的原始说明内容，默认折叠，方便先快速扫读再展开全文。</p>
        </div>
        {canCollapse ? (
          <button className="ghost-button" type="button" onClick={() => setExpanded((current) => !current)}>
            {expanded ? "收起全文" : "展开全文"}
          </button>
        ) : null}
      </div>

      <div className={`documentation-body ${canCollapse && !expanded ? "collapsed" : ""}`}>
        {documentationText}
      </div>
    </section>
  );
}

export default function FunctionWorkbench({
  detail,
  formState,
  previewRows,
  submitting,
  onPreviewRowsChange,
  onFieldChange,
  onUseDefaultChange,
  onReset,
  onExecute,
  origin,
  mcpPath,
}) {
  if (!detail) {
    return (
      <section className="frost-card empty-stage">
        <p className="eyebrow">Workspace</p>
        <h2>先在左侧选一个函数，工作台就会自动展开。</h2>
        <p>参数表单、输出结构、HTTP 示例和 MCP 接入信息都会在这里集中显示。</p>
      </section>
    );
  }

  const mcpEndpoint = mcpPath ? `${origin}${mcpPath}` : "";
  const requiredCount = detail.parameters?.filter((item) => item.required).length || 0;
  const outputCount = detail.output_parameters?.length || 0;
  const curlSnippet = `curl -X POST '${origin}/api/functions/${detail.name}/execute' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "preview_rows": ${previewRows},
    "parameters": {
      ${detail.parameters
        .slice(0, 3)
        .map((parameter) => `"${parameter.name}": ${JSON.stringify(parameter.default ?? "")}`)
        .join(",\n      ")}
    }
  }'`;

  return (
    <section className="workbench-shell">
      <header className="workspace-hero frost-card">
        <div className="workspace-hero-copy">
          <p className="eyebrow">Execution Studio</p>
          <h1>{detail.title || detail.name}</h1>
          <p className="hero-text">{detail.description || "暂无接口说明。"}</p>
          <div className="pill-row">
            <span className="tiny-pill">{detail.category}</span>
            <span className="tiny-pill soft">{detail.module}</span>
            {detail.section ? <span className="tiny-pill soft">{detail.section}</span> : null}
          </div>
        </div>

        <div className="workspace-hero-stats">
          <div className="metric-card">
            <span>函数名</span>
            <strong>{detail.name}</strong>
          </div>
          <div className="metric-card">
            <span>参数</span>
            <strong>{detail.parameters?.length || 0}</strong>
          </div>
          <div className="metric-card">
            <span>必填</span>
            <strong>{requiredCount}</strong>
          </div>
          <div className="metric-card">
            <span>输出字段</span>
            <strong>{outputCount}</strong>
          </div>
        </div>
      </header>

      <div className="workspace-layout">
        <section className="frost-card execution-panel">
          <div className="section-header section-header-split">
            <div>
              <h3>参数工作台</h3>
              <p>默认值可以保留，必要时切换为手动输入。执行前可以先调小预览行数。</p>
            </div>
            <label className="field preview-field">
              <span>预览行数</span>
              <input
                type="number"
                min="1"
                max="2000"
                value={previewRows}
                onChange={(event) => onPreviewRowsChange(event.target.value)}
              />
            </label>
          </div>

          <div className="summary-grid">
            <LongTextCard label="函数签名" value={detail.signature || "(...)"} mono />
            <LongTextCard label="目标地址" value={detail.target_url} href={detail.target_url} mono />
            <LongTextCard label="限量说明" value={detail.limit} />
          </div>

          <div className="parameter-stack">
            {detail.parameters?.length ? (
              detail.parameters.map((parameter) => {
                const fieldState = formState[parameter.name];
                return (
                  <article key={parameter.name} className="parameter-card subtle-card">
                    <div className="parameter-topline">
                      <div className="parameter-copy">
                        <div className="pill-row">
                          <strong>{parameter.name}</strong>
                          <span className="tiny-pill">{parameter.kind}</span>
                          {parameter.required ? (
                            <span className="tiny-pill important">必填</span>
                          ) : null}
                          {parameter.has_default ? (
                            <span className="tiny-pill soft">支持默认值</span>
                          ) : null}
                        </div>
                        <p>{parameter.description || parameter.annotation || "暂无参数说明"}</p>
                      </div>
                      {parameter.has_default ? (
                        <label className="toggle-line">
                          <input
                            type="checkbox"
                            checked={Boolean(fieldState?.useDefault)}
                            onChange={(event) =>
                              onUseDefaultChange(parameter.name, event.target.checked)
                            }
                          />
                          使用默认值
                        </label>
                      ) : null}
                    </div>

                    {parameter.has_default && fieldState?.useDefault ? (
                      <div className="default-banner">
                        当前使用默认值: <code>{JSON.stringify(parameter.default)}</code>
                      </div>
                    ) : null}

                    <div className={fieldState?.useDefault ? "field-lock" : ""}>
                      <FieldControl
                        parameter={parameter}
                        fieldState={fieldState}
                        onFieldChange={onFieldChange}
                      />
                    </div>

                    <div className="field-hint">
                      {parameter.choices?.length
                        ? `可选值: ${parameter.choices.join(" / ")}`
                        : parameter.default !== null && parameter.default !== undefined
                          ? `默认值: ${JSON.stringify(parameter.default)}`
                          : `参数类型: ${parameter.annotation || parameter.doc_type || parameter.kind}`}
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="empty-mini subtle-card">这个函数没有显式参数，可以直接执行。</div>
            )}
          </div>

          <div className="action-dock subtle-card">
            <div>
              <strong>准备完成后就可以执行</strong>
              <p>结果区会自动把 DataFrame 转成表格预览，JSON 或标量则直接展示原始结构。</p>
            </div>
            <div className="action-row">
              <button
                className="primary-button"
                type="button"
                disabled={submitting}
                onClick={onExecute}
              >
                {submitting ? "执行中..." : "执行函数"}
              </button>
              <button className="ghost-button" type="button" onClick={onReset}>
                重置参数
              </button>
            </div>
          </div>
        </section>

        <aside className="workspace-side">
          <section className="frost-card side-card">
            <div className="section-header">
              <div>
                <h3>接入信息</h3>
                <p>这里放调用这个接口时最需要复制和查看的关键信息。</p>
              </div>
            </div>

            <div className="info-stack">
              <LongTextCard label="MCP 端点" value={mcpEndpoint} mono />

              <div className="info-block subtle-card">
                <span className="info-label">文档分组</span>
                <div className="info-value">{detail.section || "未提供"}</div>
              </div>
            </div>
          </section>

          <section className="frost-card side-card">
            <div className="section-header">
              <div>
                <h3>调用示例</h3>
                <p>方便直接复制到命令行或 MCP 客户端里做联调。</p>
              </div>
            </div>

            <div className="info-block code-block">
              <span className="info-label">HTTP</span>
              <pre>{curlSnippet}</pre>
            </div>

            <div className="info-block code-block">
              <span className="info-label">MCP</span>
              <pre>
{mcpEndpoint
  ? `claude mcp add --transport http akshare ${mcpEndpoint}`
  : "当前服务未启用 MCP 挂载。"}
              </pre>
            </div>
          </section>

          <section className="frost-card side-card">
            <div className="section-header">
              <div>
                <h3>输出结构</h3>
                <p>执行前先看清输出字段，能更快判断后续处理方式。</p>
              </div>
            </div>
            <OutputSchema outputParameters={detail.output_parameters} />
          </section>
        </aside>
      </div>

      <DocumentationPanel detail={detail} />
    </section>
  );
}
