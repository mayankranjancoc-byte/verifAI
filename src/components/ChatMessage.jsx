import IntelCard from './IntelCard'

export default function ChatMessage({ message, onReanalyze }) {
  if (message.role === 'user') {
    return (
      <div className="msg msg--user">
        <div className="msg__bubble">
          {message.file && (
            <div className="file-preview">
              <span className="material-symbols-outlined">
                {message.file.type?.startsWith('image') ? 'image' :
                 message.file.type?.startsWith('audio') ? 'mic' :
                 message.file.type?.startsWith('video') ? 'videocam' : 'attach_file'}
              </span>
              <span>{message.file.name}</span>
            </div>
          )}
          {isUrl(message.content) ? (
            <a href={message.content} target="_blank" rel="noopener noreferrer">
              {message.content}
            </a>
          ) : (
            <span>{message.content}</span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="msg msg--ai">
      <div className="msg__bubble">
        <IntelCard
          data={message.data}
          onReanalyze={() => onReanalyze(message.data._originalQuery || '')}
        />
      </div>
    </div>
  )
}

function isUrl(str) {
  try {
    const url = new URL(str)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}
