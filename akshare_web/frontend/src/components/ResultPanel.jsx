function renderScalar(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function TableView({ columns, rows }) {
  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={`${index}-${column}`}>{renderScalar(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ResultPanel({ resultPayload, error, selectedName, selectedDetail }) {
  if (!resultPayload && !error) {
    return (
      <section className="frost-card result-panel empty-stage">
        <p className="eyebrow">Results</p>
        <h2>{selectedName ? `等待执行 ${selectedName}` : "结果区准备就绪"}</h2>
        <p>
          {selectedDetail
            ? "确认参数后点击“执行函数”，这里会按返回类型自动切换成表格或 JSON 预览。"
            : "先从目录里选一个函数，参数区和结果区都会一起准备好。"}
        </p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="frost-card result-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Execution Error</p>
            <h2>执行失败</h2>
            <p>请优先检查必填参数、日期格式和 JSON 参数格式是否正确。</p>
          </div>
        </div>
        <pre className="result-json">{error}</pre>
      </section>
    );
  }

  const result = resultPayload.result;

  return (
    <section className="frost-card result-panel">
      <div className="section-header section-header-split">
        <div>
          <p className="eyebrow">Execution Result</p>
          <h2>{resultPayload.name}</h2>
          <p>函数已成功执行，下面是结构化预览结果。</p>
        </div>
        <div className="result-metrics">
          <div className="metric-card">
            <span>耗时</span>
            <strong>{resultPayload.elapsed_ms} ms</strong>
          </div>
          <div className="metric-card">
            <span>返回类型</span>
            <strong>{result.kind}</strong>
          </div>
          <div className="metric-card">
            <span>参数数</span>
            <strong>{Object.keys(resultPayload.parameters || {}).length}</strong>
          </div>
        </div>
      </div>

      {result.kind === "dataframe" ? (
        <>
          <div className="result-summary">
            <span>已预览 {result.preview_rows.length} 行</span>
            <span>总行数 {result.total_rows}</span>
            <span>总列数 {result.total_columns}</span>
          </div>
          <TableView columns={result.columns || []} rows={result.preview_rows || []} />
        </>
      ) : null}

      {result.kind === "series" ? (
        <>
          <div className="result-summary">
            <span>已预览 {result.preview_rows.length} 行</span>
            <span>总行数 {result.total_rows}</span>
          </div>
          <TableView columns={["index", "value"]} rows={result.preview_rows || []} />
        </>
      ) : null}

      {result.kind === "sequence" ? (
        <>
          <div className="result-summary">
            <span>序列长度 {result.size}</span>
            <span>{result.truncated ? "当前仅展示部分预览" : "当前已完整展示"}</span>
          </div>
          <pre className="result-json">{JSON.stringify(result.value, null, 2)}</pre>
        </>
      ) : null}

      {result.kind === "mapping" ? (
        <pre className="result-json">{JSON.stringify(result.value, null, 2)}</pre>
      ) : null}

      {result.kind === "scalar" ? (
        <pre className="result-json">{JSON.stringify(result.value, null, 2)}</pre>
      ) : null}
    </section>
  );
}
