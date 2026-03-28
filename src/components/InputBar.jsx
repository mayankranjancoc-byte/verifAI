import { useState, useRef } from 'react'

export default function InputBar({ onSend, disabled }) {
  const [input, setInput] = useState('')
  const [file, setFile] = useState(null)
  const [recording, setRecording] = useState(false)
  const fileRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (disabled) return
    if (!input.trim() && !file) return
    onSend(input.trim(), file)
    setInput('')
    setFile(null)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
    }
  }

  const handleMic = async () => {
    if (recording) {
      // Stop recording
      mediaRecorderRef.current?.stop()
      setRecording(false)
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const audioFile = new File([blob], 'voice-note.webm', { type: 'audio/webm' })
        setFile(audioFile)
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorder.start()
      setRecording(true)
    } catch (err) {
      console.error('Mic access denied:', err)
    }
  }

  return (
    <div className="input-bar">
      <form className="input-bar__inner" onSubmit={handleSubmit}>
        <button
          type="button"
          className="input-bar__plus"
          onClick={() => fileRef.current?.click()}
        >
          <span className="material-symbols-outlined">add_circle</span>
        </button>

        <input
          ref={fileRef}
          type="file"
          accept="image/*,audio/*,video/*,.pdf,.txt,application/pdf,text/plain"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {file && (
          <div className="file-preview" style={{ position: 'absolute', bottom: '70px', left: '16px', right: '16px' }}>
            <span className="material-symbols-outlined">
              {file.type?.startsWith('image') ? 'image' :
               file.type?.startsWith('audio') ? 'mic' :
               file.type?.startsWith('video') ? 'videocam' : 'attach_file'}
            </span>
            <span>{file.name}</span>
            <span
              className="file-preview__remove material-symbols-outlined"
              onClick={() => setFile(null)}
              style={{ fontSize: '16px' }}
            >close</span>
          </div>
        )}

        <input
          className="input-bar__input"
          type="text"
          placeholder="Paste message or URL..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <button
          type="button"
          className="input-bar__mic"
          onClick={handleMic}
          style={recording ? { color: 'var(--error)', background: 'var(--error-bg)' } : {}}
        >
          <span className="material-symbols-outlined">
            {recording ? 'stop' : 'mic'}
          </span>
        </button>

        <button
          type="submit"
          className="input-bar__send"
          disabled={disabled || (!input.trim() && !file)}
        >
          <span className="material-symbols-outlined filled">send</span>
        </button>
      </form>
    </div>
  )
}
