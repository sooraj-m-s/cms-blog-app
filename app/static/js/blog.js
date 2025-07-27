const BASE_URL = window.BASE_URL || ""
let currentBlogId = null
let currentFeedbackPage = 1
let editingFeedbackId = null
let userFeedback = null

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
async function loadBlogDetail() {
  const urlParams = new URLSearchParams(window.location.search)
  currentBlogId = urlParams.get("id")

  if (!currentBlogId) {
    showNotification("Blog ID not found", "error")
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blog/${currentBlogId}/view/`)

    if (!response) return

    if (response.ok) {
      const data = await response.json()
      if (typeof window.displayBlogDetail === "function") {
        window.displayBlogDetail(data.blog)
      }
      document.getElementById("feedbackSection").classList.remove("hidden")
      loadFeedback(1)
    } else {
      showNotification("Failed to load blog", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

// Feedback functions
async function loadFeedback(page = 1) {
  try {
    const response = await makeAuthenticatedRequest(
      `${BASE_URL}/api/blogs/${currentBlogId}/feedbacks?page=${page}&page_size=10`,
    )

    if (!response) return

    if (response.ok) {
      const data = await response.json()
      if (typeof window.displayFeedback === "function") {
        window.displayFeedback(data.blogs)
      }
      if (typeof window.updateFeedbackPagination === "function") {
        window.updateFeedbackPagination(data.page, Math.ceil(data.blogs.length / 10))
      }
      currentFeedbackPage = page
    } else {
      showNotification("Failed to load feedback", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

function toggleFeedbackForm() {
  const form = document.getElementById("feedbackForm")
  const isHidden = form.classList.contains("hidden")

  if (isHidden) {
    if (userFeedback && !editingFeedbackId) {
      showNotification("You can only provide one feedback per blog", "error")
      return
    }
    form.classList.remove("hidden")
    document.getElementById("feedbackText").focus()
  } else {
    form.classList.add("hidden")
    document.getElementById("feedbackText").value = ""
    editingFeedbackId = null
  }
}

async function submitFeedback() {
  const comment = document.getElementById("feedbackText").value.trim()

  if (!comment) {
    showNotification("Please enter your feedback", "error")
    return
  }

  try {
    let response
    if (editingFeedbackId) {
      response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/feedback/${editingFeedbackId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ comment }),
      })
    } else {
      response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${currentBlogId}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ comment }),
      })
    }

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")
      cancelFeedback()
      loadFeedback(currentFeedbackPage)
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to submit feedback", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

function cancelFeedback() {
  document.getElementById("feedbackForm").classList.add("hidden")
  document.getElementById("feedbackText").value = ""
  editingFeedbackId = null
}

function editFeedback(feedbackId, currentComment) {
  editingFeedbackId = feedbackId
  document.getElementById("feedbackText").value = currentComment
  document.getElementById("feedbackForm").classList.remove("hidden")
  document.getElementById("feedbackText").focus()
}

async function deleteFeedback(feedbackId) {
  if (!confirm("Are you sure you want to delete this feedback?")) {
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/feedback/${feedbackId}`, {
      method: "DELETE",
    })

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")
      loadFeedback(currentFeedbackPage)
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to delete feedback", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

// Like/Dislike functions
async function toggleLike(blogId, button) {
  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${blogId}/like`, {
      method: "POST",
    })

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")

      const likeSpan = button.querySelector("span")
      const likeCount = Number.parseInt(likeSpan.textContent)
      const isLiked = button.classList.contains("liked")

      if (isLiked) {
        button.classList.remove("liked")
        likeSpan.textContent = likeCount - 1
      } else {
        button.classList.add("liked")
        likeSpan.textContent = likeCount + 1

        const dislikeBtn = button.nextElementSibling
        if (dislikeBtn && dislikeBtn.classList.contains("disliked")) {
          dislikeBtn.classList.remove("disliked")
          const dislikeSpan = dislikeBtn.querySelector("span")
          dislikeSpan.textContent = Number.parseInt(dislikeSpan.textContent) - 1
        }
      }
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to like blog", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

async function toggleDislike(blogId, button) {
  try {
    const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${blogId}/dislike`, {
      method: "POST",
    })

    if (!response) return

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, "success")

      const dislikeSpan = button.querySelector("span")
      const dislikeCount = Number.parseInt(dislikeSpan.textContent)
      const isDisliked = button.classList.contains("disliked")

      if (isDisliked) {
        button.classList.remove("disliked")
        dislikeSpan.textContent = dislikeCount - 1
      } else {
        button.classList.add("disliked")
        dislikeSpan.textContent = dislikeCount + 1

        const likeBtn = button.previousElementSibling
        if (likeBtn && likeBtn.classList.contains("liked")) {
          likeBtn.classList.remove("liked")
          const likeSpan = likeBtn.querySelector("span")
          likeSpan.textContent = Number.parseInt(likeSpan.textContent) - 1
        }
      }
    } else {
      const error = await response.json()
      showNotification(error.detail || "Failed to dislike blog", "error")
    }
  } catch (error) {
    showNotification("Network error. Please try again.", "error")
  }
}

// Navigation functions
function goToLanding() {
  window.location.href = `${BASE_URL}/user/landing/`
}

function goToMyBlogs() {
  window.location.href = `${BASE_URL}/user/my-blog/`
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

function setUserFeedback(feedback) {
  userFeedback = feedback
}

window.loadBlogDetail = loadBlogDetail
window.loadFeedback = loadFeedback
window.toggleFeedbackForm = toggleFeedbackForm
window.submitFeedback = submitFeedback
window.cancelFeedback = cancelFeedback
window.editFeedback = editFeedback
window.deleteFeedback = deleteFeedback
window.toggleLike = toggleLike
window.toggleDislike = toggleDislike
window.goToLanding = goToLanding
window.goToMyBlogs = goToMyBlogs
window.logout = logout
window.setUserFeedback = setUserFeedback

window.addEventListener("load", () => {
  loadBlogDetail()
})

