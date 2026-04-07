/**
 * 创建待办事项按钮组件
 * 包含按钮和模态框
 */
import { useState } from 'react'

interface Props {
  onCreate: (title: string) => void
  showModal: boolean
  setShowModal: (show: boolean) => void
}

export default function CreateTodoButton({ 
  onCreate, 
  showModal, 
  setShowModal 
}: Props) {
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!title.trim()) {
      setError('请输入待办事项标题')
      return
    }
    
    onCreate(title.trim())
    setTitle('')
    setError('')
  }

  const handleClose = () => {
    setTitle('')
    setError('')
    setShowModal(false)
  }

  return (
    <>
      {/* 创建按钮 */}
      <button
        onClick={() => setShowModal(true)}
        style={styles.createButton}
      >
        <span style={styles.buttonIcon}>+</span>
        创建待办事项
      </button>

      {/* 模态框 */}
      {showModal && (
        <div style={styles.modalOverlay} onClick={handleClose}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 style={styles.modalTitle}>新建待办事项</h2>
            
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="输入待办事项标题..."
                autoFocus
                style={styles.input}
              />
              
              {error && <p style={styles.error}>{error}</p>}
              
              <div style={styles.buttonGroup}>
                <button
                  type="button"
                  onClick={handleClose}
                  style={styles.cancelButton}
                >
                  取消
                </button>
                <button
                  type="submit"
                  style={styles.submitButton}
                >
                  确定
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  createButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 4px 6px rgba(76, 175, 80, 0.3)',
    transition: 'all 0.2s',
    width: '100%',
    justifyContent: 'center',
  },
  buttonIcon: {
    fontSize: '20px',
    fontWeight: 'bold',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '30px',
    width: '90%',
    maxWidth: '400px',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
  },
  modalTitle: {
    margin: '0 0 20px 0',
    color: '#333',
    fontSize: '20px',
    textAlign: 'center',
  },
  input: {
    width: '100%',
    padding: '12px',
    fontSize: '16px',
    border: '2px solid #e0e0e0',
    borderRadius: '6px',
    marginBottom: '10px',
    boxSizing: 'border-box',
    outline: 'none',
  },
  error: {
    color: '#ff4444',
    fontSize: '14px',
    margin: '0 0 15px 0',
  },
  buttonGroup: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'flex-end',
  },
  cancelButton: {
    padding: '10px 20px',
    backgroundColor: '#f0f0f0',
    color: '#666',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
  },
}
