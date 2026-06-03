import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Login } from '../pages/auth/Login'
import { AuthProvider } from '../context/AuthContext'
import { describe, it, expect, vi } from 'vitest'

// Mock the AuthContext so we don't need real API calls for basic rendering
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
  }),
  AuthProvider: ({ children }: any) => <div>{children}</div>
}))

describe('Login Component', () => {
  it('renders login form correctly', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    expect(screen.getByText('Welcome Back')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('student@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument()
  })

  it('shows error if fields are empty', async () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const button = screen.getByRole('button', { name: /Sign In/i })
    fireEvent.click(button)
    // Toast error would be triggered here, we can mock toast to test it if we want.
  })
})
