import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Upload, Clipboard, Copy, Check, Loader2, Image as ImageIcon } from 'lucide-react'

function App() {
    const [text, setText] = useState('')
    const [loading, setLoading] = useState(false)
    const [status, setStatus] = useState('Listo.')
    const [copied, setCopied] = useState(false)
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef(null)

    useEffect(() => {
        const handlePaste = (e) => {
            const items = (e.clipboardData || e.originalEvent.clipboardData).items
            for (let index in items) {
                const item = items[index]
                if (item.kind === 'file' && item.type.includes('image')) {
                    const blob = item.getAsFile()
                    processImage(blob)
                }
            }
        }

        window.addEventListener('paste', handlePaste)
        return () => window.removeEventListener('paste', handlePaste)
    }, [])

    const processImage = async (file) => {
        if (!file) return
        setLoading(true)
        setStatus('Procesando OCR...')
        setText('')

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await axios.post('/api/extract', formData)
            setText(response.data.text || 'No se detectó texto.')
            setStatus('¡Texto extraído con éxito!')
            if (response.data.text) {
                copyToClipboard(response.data.text, false)
            }
        } catch (error) {
            console.error(error)
            setStatus('Error al procesar la imagen.')
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
        if (file && file.type.startsWith('image/')) {
            processImage(file)
        }
    }

    const copyToClipboard = (content, notify = true) => {
        navigator.clipboard.writeText(content)
        if (notify) {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }

    return (
        <div className="App">
            <header>
                <h1>Antigravity OCR</h1>
                <p style={{ color: '#aaaaaa' }}>Pega (Ctrl+V) o arrastra una imagen para extraer texto</p>
            </header>

            <div className="glass-card">
                <div
                    className={`drop-zone ${isDragging ? 'dragging' : ''}`}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    {loading ? (
                        <div className="loading-spinner"></div>
                    ) : (
                        <>
                            <Upload size={48} color="#646cff" />
                            <p>Arrastra una imagen o haz clic para subir</p>
                            <div style={{ fontSize: '12px', color: '#666' }}>Soporta pegado directo con Ctrl+V</div>
                        </>
                    )}
                </div>

                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={(e) => processImage(e.target.files[0])}
                />

                {text && (
                    <div style={{ marginTop: '2rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '14px', color: '#888' }}>Resultado:</span>
                            <button className="copy-btn" onClick={() => copyToClipboard(text)}>
                                {copied ? <Check size={18} /> : <Copy size={18} />}
                                {copied ? '¡Copiado!' : 'Copiar'}
                            </button>
                        </div>
                        <textarea
                            className="result-area"
                            value={text}
                            readOnly
                            placeholder="El texto aparecerá aquí..."
                        ></textarea>
                    </div>
                )}

                <div className="status-msg" style={{ color: status.includes('Error') ? '#e74c3c' : '#aaaaaa' }}>
                    {status}
                </div>
            </div>
        </div>
    )
}

export default App
