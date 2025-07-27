const BASE_URL = window.BASE_URL || ""

// Form Validation functions
function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validatePassword(password) {
  return password.length >= 8
}

function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId)
  const errorElement = document.getElementById(fieldId + "Error")

  if (field && errorElement) {
    field.classList.add("error")
    errorElement.textContent = message
    errorElement.classList.add("show")
  }
}

function clearFieldError(fieldId) {
  const field = document.getElementById(fieldId)
  const errorElement = document.getElementById(fieldId + "Error")

  if (field && errorElement) {
    field.classList.remove("error")
    errorElement.classList.remove("show")
  }
}

function validateForm() {
  const emailInput = document.getElementById("email")
  const passwordInput = document.getElementById("password")

  if (!emailInput || !passwordInput) return false

  const email = emailInput.value.trim()
  const password = passwordInput.value
  let isValid = true

  // Clear previous errors
  clearFieldError("email")
  clearFieldError("password")

  // Validate email
  if (!email) {
    showFieldError("email", "Email address is required")
    isValid = false
  } else if (!validateEmail(email)) {
    showFieldError("email", "Please enter a valid email address")
    isValid = false
  }

  // Validate password
  if (!password) {
    showFieldError("password", "Password is required")
    isValid = false
  } else if (!validatePassword(password)) {
    showFieldError("password", "Password must be at least 8 characters long")
    isValid = false
  }

  return isValid
}

// Form submission handler
async function handleFormSubmit(e) {
  e.preventDefault()

  if (!validateForm()) {
    if (typeof window.showNotification === "function") {
      window.showNotification("error", "Validation Error", "Please fix the errors above and try again.")
    }
    return
  }

  const loginButton = document.getElementById("loginButton")
  const buttonText = loginButton?.querySelector(".button-text")

  if (!loginButton || !buttonText) return

  // Show loading state
  loginButton.classList.add("loading")
  loginButton.disabled = true
  buttonText.textContent = "Signing In..."

  const emailInput = document.getElementById("email")
  const passwordInput = document.getElementById("password")

  const formData = {
    email: emailInput?.value.trim() || "",
    password: passwordInput?.value || "",
  }

  try {
    const response = await fetch(`${BASE_URL}/api/admin/login/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(formData),
    })

    const data = await response.json()

    if (response.ok) {
      if (typeof window.showNotification === "function") {
        window.showNotification("success", "Login Successful", "Welcome back! Redirecting to dashboard...")
      }

      setTimeout(() => {
        window.location.href = `${BASE_URL}/admin/dashboard/`
      }, 1500)
    } else {
      let errorMessage = "Login failed. Please try again."

      if (response.status === 401) {
        errorMessage = data.detail || "Invalid email or password."
      } else if (response.status === 403) {
        errorMessage = "Admin access required. Please contact support."
      } else if (response.status === 500) {
        errorMessage = "Server error. Please try again later."
      }

      if (typeof window.showNotification === "function") {
        window.showNotification("error", "Login Failed", errorMessage)
      }
    }
  } catch (error) {
    console.error("Login error:", error)
    if (typeof window.showNotification === "function") {
      window.showNotification(
        "error",
        "Connection Error",
        "Unable to connect to the server. Please check your internet connection and try again.",
      )
    }
  } finally {
    loginButton.classList.remove("loading")
    loginButton.disabled = false
    buttonText.textContent = "Sign In"
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Email field validation
  const emailInput = document.getElementById("email")
  if (emailInput) {
    emailInput.addEventListener("blur", function () {
      const email = this.value.trim()
      if (email && !validateEmail(email)) {
        showFieldError("email", "Please enter a valid email address")
      } else if (email) {
        clearFieldError("email")
      }
    })

    emailInput.addEventListener("input", function () {
      if (this.classList.contains("error")) {
        clearFieldError("email")
      }
    })
  }

  // Password field validation
  const passwordInput = document.getElementById("password")
  if (passwordInput) {
    passwordInput.addEventListener("blur", function () {
      const password = this.value
      if (password && !validatePassword(password)) {
        showFieldError("password", "Password must be at least 8 characters long")
      } else if (password) {
        clearFieldError("password")
      }
    })

    passwordInput.addEventListener("input", function () {
      if (this.classList.contains("error")) {
        clearFieldError("password")
      }
    })
  }

  // Form submission
  const loginForm = document.getElementById("loginForm")
  if (loginForm) {
    loginForm.addEventListener("submit", handleFormSubmit)
  }
})

