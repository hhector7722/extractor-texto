import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Upload, Copy, Check, Loader2 } from 'lucide-react'

// En local: '' (Vite hace proxy a /api). En producción (Vercel): URL de tu API, ej. https://tu-api.railway.app
const API_BASE = import.meta.env.VITE_API_URL || ''

function App() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('Sube una imagen o pega con Ctrl+V')
  const [statusType, setStatusType] = useState('idle')
  const [copied, setCopied] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    const handlePaste = (e) => {
      const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          e.preventDefault()
          processImage(item.getAsFile())
          break
        }
      }
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [])

  const processImage = async (file) => {
    if (!file) return
    setLoading(true)
    setStatus('Leyendo texto de la imagen…')
    setStatusType('loading')
    setText('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const { data } = await axios.post(`${API_BASE}/api/extract`, formData)
      const result = data.text?.trim() || ''
      setText(result)
      if (result) {
        setStatus('Listo. Ya puedes copiar el texto.')
        setStatusType('success')
        copyToClipboard(result, false)
      } else {
        setStatus('No se encontró texto en la imagen.')
        setStatusType('warning')
      }
    } catch (err) {
      setStatus('Error al procesar. Comprueba que el servidor esté en marcha.')
      setStatusType('error')
    } finally {
      setLoading(false)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file?.type.startsWith('image/')) processImage(file)
  }

  const copyToClipboard = (content, notify = true) => {
    navigator.clipboard.writeText(content)
    if (notify) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Extraer texto de imagen</h1>
        <p className="app-subtitle">
          Arrastra una imagen, haz clic para elegirla o pega con <kbd>Ctrl</kbd>+<kbd>V</kbd>
        </p>
      </header>

      <main className="app-main">
        <div
          className={`drop-zone ${isDragging ? 'drop-zone--dragging' : ''} ${loading ? 'drop-zone--loading' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !loading && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !loading) {
              e.preventDefault()
              fileInputRef.current?.click()
            }
          }}
          aria-label="Subir imagen para extraer texto"
        >
          {loading ? (
            <div className="drop-zone-loading">
              <Loader2 className="drop-zone-icon drop-zone-icon--spin" size={56} aria-hidden />
              <span className="drop-zone-loading-text">Procesando…</span>
            </div>
          ) : (
            <>
              <Upload className="drop-zone-icon" size={56} aria-hidden />
              <span className="drop-zone-label">Suelta aquí la imagen</span>
              <span className="drop-zone-hint">o haz clic para seleccionar un archivo</span>
            </>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          className="file-input"
          accept="image/*"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) processImage(f)
            e.target.value = ''
          }}
          aria-label="Seleccionar imagen"
        />

        {text && (
          <section className="result-section" aria-label="Texto extraído">
            <div className="result-header">
              <span className="result-label">Texto extraído</span>
              <button
                type="button"
                className="btn btn--copy"
                onClick={() => copyToClipboard(text)}
                aria-label={copied ? 'Copiado' : 'Copiar al portapapeles'}
              >
                {copied ? (
                  <>
                    <Check size={20} aria-hidden />
                    <span>Copiado</span>
                  </>
                ) : (
                  <>
                    <Copy size={20} aria-hidden />
                    <span>Copiar</span>
                  </>
                )}
              </button>
            </div>
            <textarea
              className="result-area"
              value={text}
              readOnly
              rows={8}
              aria-label="Texto extraído de la imagen"
            />
          </section>
        )}

        <p className={`status status--${statusType}`} role="status">
          {status}
        </p>
      </main>
    </div>
  )
}

export default App
