/**
 * 创建待办事项按钮组件测试
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import CreateTodoButton from './CreateTodoButton'

describe('CreateTodoButton', () => {
  const mockOnCreate = vi.fn()
  const mockSetShowModal = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('渲染创建按钮', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={false}
        setShowModal={mockSetShowModal}
      />
    )

    const button = screen.getByText('创建待办事项')
    expect(button).toBeInTheDocument()
  })

  it('点击按钮打开模态框', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={false}
        setShowModal={mockSetShowModal}
      />
    )

    fireEvent.click(screen.getByText('创建待办事项'))
    expect(mockSetShowModal).toHaveBeenCalledWith(true)
  })

  it('显示模态框', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    expect(screen.getByText('新建待办事项')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入待办事项标题...')).toBeInTheDocument()
  })

  it('输入标题并提交', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    const input = screen.getByPlaceholderText('输入待办事项标题...')
    fireEvent.change(input, { target: { value: '测试待办' } })

    fireEvent.click(screen.getByText('确定'))

    expect(mockOnCreate).toHaveBeenCalledWith('测试待办')
  })

  it('空标题显示错误', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    fireEvent.click(screen.getByText('确定'))

    expect(screen.getByText('请输入待办事项标题')).toBeInTheDocument()
    expect(mockOnCreate).not.toHaveBeenCalled()
  })

  it('点击取消关闭模态框', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    fireEvent.click(screen.getByText('取消'))

    expect(mockSetShowModal).toHaveBeenCalledWith(false)
  })

  it('点击遮罩层关闭模态框', () => {
    render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    fireEvent.click(screen.getByRole('dialog').parentElement!)

    expect(mockSetShowModal).toHaveBeenCalledWith(false)
  })

  it('提交后清空输入框', () => {
    const { container } = render(
      <CreateTodoButton
        onCreate={mockOnCreate}
        showModal={true}
        setShowModal={mockSetShowModal}
      />
    )

    const input = screen.getByPlaceholderText('输入待办事项标题...') as HTMLInputElement
    fireEvent.change(input, { target: { value: '测试待办' } })
    fireEvent.click(screen.getByText('确定'))

    expect(input.value).toBe('')
  })
})
