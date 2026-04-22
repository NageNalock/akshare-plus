export default function CataloguePane({
  filteredItems,
  selectedName,
  selectedItem,
  onSelect,
}) {
  return (
    <aside className="catalogue-panel frost-card">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Function Browser</p>
          <h2>函数目录</h2>
        </div>
        <div className="count-badge">{filteredItems.length}</div>
      </div>

      {selectedItem ? (
        <div className="spotlight-card subtle-card">
          <span className="spotlight-label">当前焦点</span>
          <strong>{selectedItem.title || selectedItem.name}</strong>
          <p>{selectedItem.description || "这个函数已经准备好在右侧工作台里执行。"}</p>
          <div className="pill-row">
            <span className="tiny-pill">{selectedItem.category}</span>
            <span className="tiny-pill soft">{selectedItem.module}</span>
            {selectedItem.section ? (
              <span className="tiny-pill soft">{selectedItem.section}</span>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="catalogue-list">
        {filteredItems.length ? (
          filteredItems.map((item) => (
            <button
              key={item.name}
              type="button"
              className={`catalogue-item ${item.name === selectedName ? "active" : ""}`}
              onClick={() => onSelect(item.name)}
            >
              <div className="catalogue-item-head">
                <div>
                  <strong>{item.title || item.name}</strong>
                  <code>{item.name}</code>
                </div>
                <span className="tiny-pill">{item.category}</span>
              </div>
              <p>{item.description || item.signature || "暂无描述"}</p>
              <div className="pill-row">
                <span className="tiny-pill soft">{item.module}</span>
                {item.section ? <span className="tiny-pill soft">{item.section}</span> : null}
              </div>
            </button>
          ))
        ) : (
          <div className="empty-mini subtle-card">没有命中的函数，试试换个关键词或分类。</div>
        )}
      </div>
    </aside>
  );
}
