const BASE_URL = window.BASE_URL || ""
let currentPage = 1
let isLoading = false
let editingBlogId = null

// Utility functions
function showNotification(message, type = "success") {
  const notification = document.createElement("div")
  notification.className = `notification ${type}`
  notification.textContent = message

  if (document.body) {
    document.body.appendChild(notification)

    setTimeout(() => notification.classList.add("show"), 100)
    setTimeout(() => {
      notification.classList.remove("show")
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification)
        }
      }, 300)
    }, 3000)
  }
}

// Authentication helper
async function makeAuthenticatedRequest(url, options = {}) {
  try {
    let response = await fetch(url, {
      ...options,
      credentials: "include",
    })

    if (response.status === 401) {
      console.log("Access token expired, trying to refresh...")

      const refreshResponse = await fetch(`${BASE_URL}/api/refresh/`, {
        method: "POST",
        credentials: "include",
      })

      if (refreshResponse.ok) {
        console.log("Token refreshed successfully, retrying original request...")
        response = await fetch(url, {
          ...options,
          credentials: "include",
        })
      } else {
        console.log("Refresh failed, redirecting to login...")
        showNotification("Session expired. Please login again.", "error")
        setTimeout(() => {
          window.location.href = `${BASE_URL}/user/login/`
        }, 1500)
        return null
      }
    }

    return response
  } catch (error) {
    console.error("Request failed:", error)
    throw error
  }
}

// Blog loading function
async function loadMyBlogs(page = 1) {
  if (isLoading) return
  isLoading = true

  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/?page=${page}&page_size=10`)

    if (!response) return

    if (response.ok) {
      const data = await response.json()
      if (typeof window.displayBlogs === "function") {
        window.displayBlogs(data.blogs.blogs)
      }
      if (typeof window.updatePagination === "function") {
        window.updatePagination(data.blogs.page, Math.ceil(data.blogs.blogs.length / 10))
      }
      currentPage = page
    } else {
      showNotification("Failed to load blogs", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  } finally {
    isLoading = false
  }
}

// Modal functions
function openCreateModal() {
  editingBlogId = null
  document.getElementById("modalTitle").textContent = "Create New Blog"
  document.getElementById("submitBtn").textContent = "Create Blog"
  document.getElementById("blogForm").reset()
  document.getElementById("fileDisplayText").textContent = "Click to select an image or drag and drop"
  clearErrors()
  document.getElementById("blogModal").classList.add("show")
}

async function editBlog(blogId) {
  editingBlogId = blogId
  document.getElementById("modalTitle").textContent = "Edit Blog"
  document.getElementById("submitBtn").textContent = "Update Blog"

  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blog/${blogId}/view/`)

    if (!response) return

    if (response.ok) {
      const data = await response.json()
      const blog = data.blog

      document.getElementById("blogTitle").value = blog.title
      document.getElementById("blogContent").value = blog.content
      document.getElementById("fileDisplayText").textContent = blog.image_url
        ? "Current image will be kept (select new to replace)"
        : "Click to select an image or drag and drop"

      clearErrors()
      document.getElementById("blogModal").classList.add("show")
    } else {
      showNotification("Failed to load blog data", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

function closeModal() {
  document.getElementById("blogModal").classList.remove("show")
  document.getElementById("blogForm").reset()
  editingBlogId = null
  clearErrors()
}

function clearErrors() {
  const errorElements = document.querySelectorAll(".error-text")
  errorElements.forEach((el) => {
    if (el) el.textContent = ""
  })
}

// Form validation
function validateBlogForm() {
  clearErrors()
  let isValid = true

  const title = document.getElementById("blogTitle").value.trim()
  const content = document.getElementById("blogContent").value.trim()
  const image = document.getElementById("blogImage").files[0]

  if (title.length < 4) {
    const titleError = document.getElementById("titleError")
    if (titleError) titleError.textContent = "Title must be at least 4 characters"
    isValid = false
  }

  if (content.length < 10) {
    const contentError = document.getElementById("contentError")
    if (contentError) contentError.textContent = "Content must be at least 10 characters"
    isValid = false
  }

  if (image && image.size > 5 * 1024 * 1024) {
    const imageError = document.getElementById("imageError")
    if (imageError) imageError.textContent = "Image size must be less than 5MB"
    isValid = false
  }

  return isValid
}

// Form submission
async function handleBlogSubmit(event) {
  event.preventDefault()

  if (!validateBlogForm()) {
    return
  }

  const submitBtn = document.getElementById("submitBtn")
  if (!submitBtn) return

  const originalText = submitBtn.textContent
  submitBtn.disabled = true
  submitBtn.textContent = editingBlogId ? "Updating..." : "Creating..."

  const formData = new FormData()
  formData.append("title", document.getElementById("blogTitle").value.trim())
  formData.append("content", document.getElementById("blogContent").value.trim())

  const imageFile = document.getElementById("blogImage").files[0]
  if (imageFile) {
    formData.append("image", imageFile)
  }

  try {
    let response
    if (editingBlogId) {
      response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${editingBlogId}`, {
        method: "PATCH",
        body: formData,
      })
    } else {
      response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/`, {
        method: "POST",
        body: formData,
      })
    }

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")
      closeModal()
      loadMyBlogs(currentPage)
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to save blog", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  } finally {
    submitBtn.disabled = false
    submitBtn.textContent = originalText
  }
}

// Blog management functions
async function deleteBlog(blogId) {
  if (!confirm("Are you sure you want to delete this blog? This action cannot be undone.")) {
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${blogId}/delete/`, {
      method: "DELETE",
    })

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")
      loadMyBlogs(currentPage)
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to delete blog", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

function viewBlog(blogId) {
  window.location.href = `${BASE_URL}/user/blog-detail/?id=${blogId}`
}

// Navigation functions
function goToLanding() {
  window.location.href = `${BASE_URL}/user/landing/`
}

// Logout function
async function logout() {
  try {
    const response = await fetch(`${BASE_URL}/api/logout/`, {
      method: "POST",
      credentials: "include",
    })

    if (response.ok) {
      showNotification("Logged out successfully", "success")
      setTimeout(() => {
        window.location.href = `${BASE_URL}/user/login/`
      }, 1000)
    } else {
      showNotification("Logout failed", "error")
    }
  } catch (error) {
    showNotification("Network error", "error")
  }
}

window.loadMyBlogs = loadMyBlogs
window.openCreateModal = openCreateModal
window.editBlog = editBlog
window.closeModal = closeModal
window.handleBlogSubmit = handleBlogSubmit
window.deleteBlog = deleteBlog
window.viewBlog = viewBlog
window.goToLanding = goToLanding
window.logout = logout

document.addEventListener("DOMContentLoaded", () => {
  // File input handling
  const blogImageInput = document.getElementById("blogImage")
  if (blogImageInput) {
    blogImageInput.addEventListener("change", (e) => {
      const file = e.target.files[0]
      const displayText = document.getElementById("fileDisplayText")

      if (file && displayText) {
        displayText.textContent = `Selected: ${file.name}`
      } else if (displayText) {
        displayText.textContent = "Click to select an image or drag and drop"
      }
    })
  }

  // Close modal when clicking outside
  const blogModal = document.getElementById("blogModal")
  if (blogModal) {
    blogModal.addEventListener("click", function (e) {
      if (e.target === this) {
        closeModal()
      }
    })
  }
})

window.addEventListener("load", () => {
  loadMyBlogs(1)
})

