const BASE_URL = window.BASE_URL || ""

let currentTab = "users"
const currentPage = {
  users: 1,
  blogs: 1,
  feedbacks: 1,
}
let currentBlogId = null

// Token Manager Class
class TokenManager {
  static async makeRequest(url, options = {}) {
    try {
      console.log(`Making request to: ${url}`)

      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        credentials: "include",
      })

      console.log(`Response status: ${response.status}`)

      // If unauthorized (401), try to refresh token
      if (response.status === 401) {
        console.log("Access token expired, attempting refresh...")
        const refreshed = await this.refreshToken()

        if (refreshed) {
          console.log("Token refreshed successfully, retrying request...")
          // Retry original request with new token
          return await fetch(url, {
            ...options,
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
              ...options.headers,
            },
          })
        } else {
          console.log("Token refresh failed, redirecting to login")
          this.redirectToLogin()
          return null
        }
      }

      return response
    } catch (error) {
      console.error("Request failed:", error)
      showNotification("error", "Network error occurred")
      return null
    }
  }

  static async refreshToken() {
    try {
      console.log("Attempting to refresh token...")
      const response = await fetch(`${BASE_URL}/api/refresh/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      })

      if (response.ok) {
        console.log("Token refreshed successfully")
        return true
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.log("Token refresh failed:", errorData)
        return false
      }
    } catch (error) {
      console.error("Token refresh error:", error)
      return false
    }
  }

  static redirectToLogin() {
    showNotification("warning", "Session expired. Please login again.")
    setTimeout(() => {
      window.location.href = `${BASE_URL}/admin/login/`
    }, 2000)
  }
}

// Notification System
function showNotification(type, message) {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.textContent = message
  document.body.appendChild(notification)

  setTimeout(() => notification.classList.add("show"), 100)
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => notification.remove(), 300)
  }, 3000)
}

// Tab Management
function switchTab(tabName) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"))
  event.target.classList.add("active")

  document.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"))
  document.getElementById(`${tabName}-tab`).classList.add("active")

  currentTab = tabName

  if (tabName === "users") {
    loadUsers()
  } else if (tabName === "blogs") {
    loadBlogs()
  }
}

// Users Management
async function loadUsers(page = 1) {
  const loading = document.getElementById("users-loading")
  const table = document.getElementById("users-table")

  loading.classList.add("show")
  table.style.display = "none"

  const response = await TokenManager.makeRequest(`${BASE_URL}/api/admin/list-users/?page=${page}&page_size=10`, {
    method: "GET",
    credentials: "include",
  })

  if (response && response.ok) {
    const data = await response.json()
    if (typeof window.displayUsers === "function") {
      window.displayUsers(data.users)
    }
    if (typeof window.createPagination === "function") {
      window.createPagination("users-pagination", data.page, data.total_pages, loadUsers)
    }
    currentPage.users = page

    loading.classList.remove("show")
    table.style.display = "table"
  } else {
    loading.classList.remove("show")
    if (response) {
      const errorData = await response.json().catch(() => ({}))
      showNotification("error", errorData.detail || "Failed to load users")
    } else {
      showNotification("error", "Failed to load users - no response")
    }
  }
}

async function toggleUserBlock(userId, isBlocked) {
  const response = await TokenManager.makeRequest(`${BASE_URL}/api/admin/block-unblock-user/${userId}`, {
    method: "PATCH",
    credentials: "include",
  })

  if (response && response.ok) {
    const data = await response.json()
    showNotification("success", data.message)
    loadUsers(currentPage.users)
  } else {
    showNotification("error", "Failed to update user status")
  }
}

// Blogs Management
async function loadBlogs(page = 1) {
  const loading = document.getElementById("blogs-loading")
  const table = document.getElementById("blogs-table")

  loading.classList.add("show")
  table.style.display = "none"

  const response = await TokenManager.makeRequest(`${BASE_URL}/api/admin/landing/?page=${page}&page_size=10`, {
    method: "GET",
    credentials: "include",
  })

  if (response && response.ok) {
    const data = await response.json()
    if (typeof window.displayBlogs === "function") {
      window.displayBlogs(data.blogs)
    }
    if (typeof window.createPagination === "function") {
      window.createPagination("blogs-pagination", data.page, data.total_pages, loadBlogs)
    }
    currentPage.blogs = page

    loading.classList.remove("show")
    table.style.display = "table"
  } else {
    loading.classList.remove("show")
    if (response) {
      const errorData = await response.json().catch(() => ({}))
      showNotification("error", errorData.detail || "Failed to load blogs")
    }
  }
}

async function toggleBlogBlock(blogId, isBlocked) {
  const response = await TokenManager.makeRequest(`${BASE_URL}/api/admin/blogs/${blogId}/block/`, {
    method: "PATCH",
    credentials: "include",
  })

  if (response && response.ok) {
    const data = await response.json()
    showNotification("success", data.message)
    loadBlogs(currentPage.blogs)
  } else {
    showNotification("error", "Failed to update blog status")
  }
}

// Feedbacks Management
async function loadFeedbacks(page = 1) {
  const blogIdInput = document.getElementById("blog-id-input")
  const blogId = blogIdInput.value.trim()

  if (!blogId) {
    showNotification("warning", "Please enter a Blog ID")
    return
  }

  currentBlogId = blogId
  const loading = document.getElementById("feedbacks-loading")
  const table = document.getElementById("feedbacks-table")

  loading.classList.add("show")
  table.style.display = "none"

  const response = await TokenManager.makeRequest(
    `${BASE_URL}/api/admin/feedbacks/${blogId}/?page=${page}&page_size=10`,
    {
      method: "PATCH",
      credentials: "include",
    },
  )

  if (response && response.ok) {
    const data = await response.json()
    if (typeof window.displayFeedbacks === "function") {
      window.displayFeedbacks(data.feedbacks)
    }
    if (typeof window.createPagination === "function") {
      window.createPagination("feedbacks-pagination", data.page, data.total_pages, loadFeedbacks)
    }
    currentPage.feedbacks = page

    loading.classList.remove("show")
    table.style.display = "table"
  } else {
    loading.classList.remove("show")
    if (response) {
      const errorData = await response.json().catch(() => ({}))
      showNotification("error", errorData.detail || "Failed to load feedbacks")
    }
  }
}

async function toggleFeedbackListed(feedbackId, isListed) {
  const response = await TokenManager.makeRequest(`${BASE_URL}/api/admin/feedbacks/${feedbackId}/toggle/`, {
    method: "PATCH",
    credentials: "include",
  })

  if (response && response.ok) {
    const data = await response.json()
    showNotification("success", data.message)
    loadFeedbacks(currentPage.feedbacks)
  } else {
    showNotification("error", "Failed to update feedback status")
  }
}

// Logout Function
async function logout() {
  try {
    const response = await fetch(`${BASE_URL}/api/logout/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    })

    if (response.ok) {
      showNotification("success", "Logged out successfully")
    } else {
      showNotification("warning", "Logout completed")
    }
  } catch (error) {
    console.error("Logout error:", error)
    showNotification("warning", "Logout completed")
  }

  setTimeout(() => {
    window.location.href = `${BASE_URL}/admin/login/`
  }, 1000)
}

window.switchTab = switchTab
window.loadUsers = loadUsers
window.toggleUserBlock = toggleUserBlock
window.loadBlogs = loadBlogs
window.toggleBlogBlock = toggleBlogBlock
window.loadFeedbacks = loadFeedbacks
window.toggleFeedbackListed = toggleFeedbackListed
window.logout = logout

document.addEventListener("DOMContentLoaded", () => {
  console.log("Admin Dashboard loaded - using httpOnly cookies")

  const blogsSearch = document.getElementById("blogs-search")
  if (blogsSearch) {
    blogsSearch.addEventListener("input", (e) => {
      console.log("Searching blogs:", e.target.value)
    })
  }

  loadUsers()
})

