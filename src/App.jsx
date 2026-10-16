import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL

const EMPTY_FORM = {
  date: '',
  startTime: '',
  endTime: '',
  cashTips: '',
  creditTips: '',
}

function calculateShiftHours(startTime, endTime) {
  const [startHour, startMinute] = startTime.split(':').map(Number)
  const [endHour, endMinute] = endTime.split(':').map(Number)

  const startInMinutes = startHour * 60 + startMinute
  let endInMinutes = endHour * 60 + endMinute

  if (endInMinutes < startInMinutes) {
    endInMinutes += 24 * 60
  }

  return (endInMinutes - startInMinutes) / 60
}

// Displays one dashboard statistic, such as total tips or hours worked.
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

// Collects the user's shift details and sends the completed form data to App.
function ShiftForm({ onAddShift }) {
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  function handleInputChange(event) {
    const { name, value } = event.target

    setFormData((currentFormData) => ({
      ...currentFormData,
      [name]: value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (isSubmitting) {
      return
    }

    setIsSubmitting(true)
    setErrorMessage('')

    const newShift = {
      date: formData.date,
      startTime: formData.startTime,
      endTime: formData.endTime,
      cashTips: Number(formData.cashTips),
      creditTips: Number(formData.creditTips),
    }

    try {
      await onAddShift(newShift)
      setFormData(EMPTY_FORM)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to add shift')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="panel shift-form-panel" aria-labelledby="add-shift-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">New entry</p>
          <h2 id="add-shift-title">Add a shift</h2>
        </div>
        <span className="draft-badge">Draft</span>
      </div>

      <form className="shift-form" onSubmit={handleSubmit}>
        <label className="field field-wide">
          <span>Shift date</span>
          <input
            type="date"
            name="date"
            required
            value={formData.date}
            onChange={handleInputChange}
          />
        </label>

        <label className="field">
          <span>Clock in</span>
          <input
            type="time"
            name="startTime"
            required
            value={formData.startTime}
            onChange={handleInputChange}
          />
        </label>

        <label className="field">
          <span>Clock out</span>
          <input
            type="time"
            name="endTime"
            required
            value={formData.endTime}
            onChange={handleInputChange}
          />
        </label>

        <label className="field">
          <span>Cash tips</span>
          <div className="money-input">
            <span>$</span>
            <input
              type="number"
              name="cashTips"
              min="0"
              step="0.01"
              placeholder="0.00"
              required
              value={formData.cashTips}
              onChange={handleInputChange}
            />
          </div>
        </label>

        <label className="field">
          <span>Credit card tips</span>
          <div className="money-input">
            <span>$</span>
            <input
              type="number"
              name="creditTips"
              min="0"
              step="0.01"
              placeholder="0.00"
              required
              value={formData.creditTips}
              onChange={handleInputChange}
            />
          </div>
        </label>

        {errorMessage && (
          <p className="form-error" role="alert">
            {errorMessage}
          </p>
        )}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Add shift'}
        </button>
      </form>
    </section>
  )
}

// Displays one saved shift and provides a control for deleting it.
function ShiftItem({ shift, onDeleteShift, deletingShiftId }) {
  const totalTips = shift.cashTips + shift.creditTips
  const isDeleting = deletingShiftId === shift.id
  const formattedDate = new Date(`${shift.date}T00:00:00`).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })

  return (
    <article className="shift-item">
      <div className="shift-date">
        <strong>{formattedDate}</strong>
        <span>{shift.startTime} – {shift.endTime}</span>
      </div>

      <div className="shift-tip-details">
        <span>Cash ${shift.cashTips.toFixed(2)}</span>
        <span>Card ${shift.creditTips.toFixed(2)}</span>
      </div>

      <div className="shift-total">
        <span>Total tips</span>
        <strong>${totalTips.toFixed(2)}</strong>
      </div>

      <button
        className="delete-button"
        type="button"
        disabled={deletingShiftId !== null}
        onClick={() => onDeleteShift(shift.id)}
        aria-label={`Delete shift from ${formattedDate}`}
      >
        {isDeleting ? 'Deleting...' : 'Delete'}
      </button>
    </article>
  )
}

// Displays the loading, error, empty, or saved-shift state of the history panel.
function ShiftHistory({
  shifts,
  isLoading,
  errorMessage,
  deleteError,
  onDeleteShift,
  deletingShiftId,
}) {
  return (
    <section className="panel history-panel" aria-labelledby="shift-history-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">This week</p>
          <h2 id="shift-history-title">Shift history</h2>
        </div>
        <button className="text-button" type="button">View all</button>
      </div>

      {deleteError && (
        <p className="delete-error" role="alert">
          {deleteError}
        </p>
      )}

      {isLoading ? (
        <div className="empty-state" aria-live="polite">
          <h3>Loading shifts...</h3>
          <p>Retrieving your saved shifts from AWS.</p>
        </div>
      ) : errorMessage ? (
        <div className="empty-state" role="alert">
          <div className="empty-icon" aria-hidden="true">!</div>
          <h3>Unable to load shifts</h3>
          <p>{errorMessage}</p>
        </div>
      ) : shifts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon" aria-hidden="true">☕</div>
          <h3>No shifts recorded yet</h3>
          <p>Your shifts will appear here after you add your first one.</p>
        </div>
      ) : (
        <div className="shift-list">
          {shifts.map((shift) => (
            <ShiftItem
              key={shift.id}
              shift={shift}
              onDeleteShift={onDeleteShift}
              deletingShiftId={deletingShiftId}
            />
          ))}
        </div>
      )}
    </section>
  )
}

// Owns the shift data, communicates with the AWS API, and assembles the dashboard.
function App() {
  const [shifts, setShifts] = useState([])
  const [isLoadingShifts, setIsLoadingShifts] = useState(true)
  const [shiftLoadError, setShiftLoadError] = useState('')
  const [deletingShiftId, setDeletingShiftId] = useState(null)
  const [deleteError, setDeleteError] = useState('')

  // Load saved shifts from AWS once when the application starts.
  useEffect(() => {
    async function loadShifts() {
      if (!API_URL) {
        setShiftLoadError('VITE_API_URL is not configured')
        setIsLoadingShifts(false)
        return
      }

      try {
        const response = await fetch(API_URL)
        const responseData = await response.json()

        if (!response.ok) {
          throw new Error(responseData.error || 'Unable to load shifts')
        }

        if (!Array.isArray(responseData.shifts)) {
          throw new Error('The API returned an invalid shift list')
        }

        setShifts(responseData.shifts)
      } catch (error) {
        setShiftLoadError(
          error instanceof Error ? error.message : 'Unable to load shifts',
        )
      } finally {
        setIsLoadingShifts(false)
      }
    }

    loadShifts()
  }, [])

  const totalTips = shifts.reduce(
    (sum, shift) => sum + shift.cashTips + shift.creditTips,
    0,
  )

  const totalHours = shifts.reduce(
    (sum, shift) => sum + calculateShiftHours(shift.startTime, shift.endTime),
    0,
  )

  const tipsPerHour = totalHours > 0 ? totalTips / totalHours : 0

  async function handleAddShift(newShift) {
    if (!API_URL) {
      throw new Error('VITE_API_URL is not configured')
    }

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newShift),
    })

    const responseData = await response.json()

    if (!response.ok) {
      throw new Error(responseData.error || 'Unable to save shift')
    }

    setShifts((currentShifts) => [responseData.shift, ...currentShifts])
  }

  // Confirm the choice, delete the shift in AWS, and remove it from React state.
  async function handleDeleteShift(shiftId) {
    if (deletingShiftId !== null) {
      return
    }

    const shouldDelete = window.confirm(
      'Are you sure you want to delete this shift?',
    )

    if (!shouldDelete) {
      return
    }

    setDeleteError('')

    if (!API_URL) {
      setDeleteError('VITE_API_URL is not configured')
      return
    }

    setDeletingShiftId(shiftId)

    try {
      const response = await fetch(`${API_URL}/${encodeURIComponent(shiftId)}`, {
        method: 'DELETE',
      })
      const responseData = await response.json()

      if (!response.ok) {
        throw new Error(responseData.error || 'Unable to delete shift')
      }

      setShifts((currentShifts) =>
        currentShifts.filter((shift) => shift.id !== shiftId),
      )
    } catch (error) {
      setDeleteError(
        error instanceof Error ? error.message : 'Unable to delete shift',
      )
    } finally {
      setDeletingShiftId(null)
    }
  }

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
          <SummaryCard
            label="Total tips"
            value={`$${totalTips.toFixed(2)}`}
            detail="Cash + card"
            accent="green"
          />
          <SummaryCard
            label="Hours worked"
            value={totalHours.toFixed(1)}
            detail={`Across ${shifts.length} ${shifts.length === 1 ? 'shift' : 'shifts'}`}
            accent="orange"
          />
          <SummaryCard
            label="Tips per hour"
            value={`$${tipsPerHour.toFixed(2)}`}
            detail="Weekly average"
            accent="blue"
          />
        </section>

        <div className="content-grid">
          <ShiftForm onAddShift={handleAddShift} />
          <ShiftHistory
            shifts={shifts}
            isLoading={isLoadingShifts}
            errorMessage={shiftLoadError}
            deleteError={deleteError}
            onDeleteShift={handleDeleteShift}
            deletingShiftId={deletingShiftId}
          />
        </div>
      </main>
    </div>
  )
}

export default App
