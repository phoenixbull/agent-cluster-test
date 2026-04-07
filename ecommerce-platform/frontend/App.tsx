/**
 * 待办事项应用 - 创建按钮演示
 */
import { useState } from 'react'
import CreateTodoButton from './CreateTodoButton'

interface Todo {
  id: number
  title: string
  completed: boolean
}

function App() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [showModal, setShowModal] = useState(false)

  const handleCreateTodo = (title: string) => {
    const newTodo: Todo = {
      id: Date.now(),
      title,
      completed: false,
    }
    setTodos([...todos, newTodo])
    setShowModal(false)
  }

  const handleDeleteTodo = (id: number) => {
    setTodos(todos.filter(todo => todo.id !== id))
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>📝 待办事项</h1>
      
      {/* 创建按钮 */}
      <CreateTodoButton 
        onCreate={handleCreateTodo}
        showModal={showModal}
        setShowModal={setShowModal}
      />
      
      {/* 待办列表 */}
      <div style={styles.todoList}>
        {todos.length === 0 ? (
          <p style={styles.empty}>暂无待办事项</p>
        ) : (
          todos.map(todo => (
            <div key={todo.id} style={styles.todoItem}>
              <span style={styles.todoTitle}>
                {todo.completed ? '✅' : '⬜'} {todo.title}
              </span>
              <button
                onClick={() => handleDeleteTodo(todo.id)}
                style={styles.deleteBtn}
              >
                删除
              </button>
            </div>
          ))
        )}
      </div>
      
      {/* 统计 */}
      {todos.length > 0 && (
        <div style={styles.stats}>
          总计：{todos.length} 项
        </div>
      )}
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '600px',
    margin: '40px auto',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
  },
  title: {
    textAlign: 'center',
    color: '#333',
    marginBottom: '30px',
  },
  todoList: {
    marginTop: '20px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
    padding: '15px',
  },
  todoItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px',
    marginBottom: '8px',
    backgroundColor: 'white',
    borderRadius: '6px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  todoTitle: {
    fontSize: '16px',
    color: '#555',
  },
  deleteBtn: {
    padding: '6px 12px',
    backgroundColor: '#ff4444',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  empty: {
    textAlign: 'center',
    color: '#999',
    padding: '20px',
  },
  stats: {
    marginTop: '15px',
    textAlign: 'center',
    color: '#666',
    fontSize: '14px',
  },
}

export default App
