import './App.css'

function SummaryCard({ label, value, detail, accent }) {
  return (
    <article className="summary-card">
      <div className={`summary-icon ${accent}`} aria-hidden="true">
        {accent === 'green' ? '$' : accent === 'orange' ? '☀' : '↗'}
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </article>
  )
}

function ShiftForm() {
  return (
    <section className="panel shift-form-panel" aria-labelledby="add-shift-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">New entry</p>
          <h2 id="add-shift-title">Add a shift</h2>
        </div>
        <span className="draft-badge">Draft</span>
      </div>

      <form className="shift-form">
        <label className="field field-wide">
          <span>Shift date</span>
          <input type="date" name="date" />
        </label>

        <label className="field">
          <span>Clock in</span>
          <input type="time" name="startTime" />
        </label>

        <label className="field">
          <span>Clock out</span>
          <input type="time" name="endTime" />
        </label>

        <label className="field">
          <span>Cash tips</span>
          <div className="money-input">
            <span>$</span>
            <input type="number" name="cashTips" min="0" step="0.01" placeholder="0.00" />
          </div>
        </label>

        <label className="field">
          <span>Credit card tips</span>
          <div className="money-input">
            <span>$</span>
            <input type="number" name="creditTips" min="0" step="0.01" placeholder="0.00" />
          </div>
        </label>

        <button className="primary-button" type="button">
          Add shift
        </button>
      </form>
    </section>
  )
}

function ShiftHistory() {
  return (
    <section className="panel history-panel" aria-labelledby="shift-history-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">This week</p>
          <h2 id="shift-history-title">Shift history</h2>
        </div>
        <button className="text-button" type="button">View all</button>
      </div>

      <div className="empty-state">
        <div className="empty-icon" aria-hidden="true">☕</div>
        <h3>No shifts recorded yet</h3>
        <p>Your shifts will appear here after you add your first one.</p>
      </div>
    </section>
  )
}

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand" href="#top" aria-label="Tip Tracker home">
          <span className="brand-mark">T</span>
          <span>Tip Tracker</span>
        </a>
        <div className="profile" aria-label="Current user">
          <span>SC</span>
          <div>
            <strong>Shane</strong>
            <small>Server</small>
          </div>
        </div>
      </header>

      <main id="top" className="dashboard">
        <section className="welcome">
          <div>
            <p className="eyebrow">Weekly overview</p>
            <h1>Keep tabs on every shift.</h1>
            <p>Record your hours and tips, then see what your work is worth.</p>
          </div>
          <div className="week-label">
            <span>This week</span>
            <strong>Jul 29 – Aug 4</strong>
          </div>
        </section>

        <section className="summary-grid" aria-label="Weekly summary">
          <SummaryCard label="Total tips" value="$0.00" detail="Cash + card" accent="green" />
          <SummaryCard label="Hours worked" value="0.0" detail="Across 0 shifts" accent="orange" />
          <SummaryCard label="Tips per hour" value="$0.00" detail="Weekly average" accent="blue" />
        </section>

        <div className="content-grid">
          <ShiftForm />
          <ShiftHistory />
        </div>
      </main>
    </div>
  )
}

export default App
