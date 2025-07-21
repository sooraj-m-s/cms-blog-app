const lucide = {
  createIcons: () => {
    console.log("Lucide icons created")
  },
}

let currentToken = null
let currentBlogId = null
let currentUserFeedback = null
let currentView = "all"
let editingBlogId = null

// Initialize page
document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons()
  checkAuth()
  setupDragAndDrop()
})

// Toast Notification System
function showToast(message, type = "info", duration = 5000) {
  const toastContainer = document.getElementById("toastContainer")
  const toast = document.createElement("div")
  toast.className = `toast ${type}`

  let iconName = "info"
  let iconColor = "#3b82f6"

  switch (type) {
    case "success":
      iconName = "check-circle"
      iconColor = "#10b981"
      break
    case "error":
      iconName = "x-circle"
      iconColor = "#ef4444"
      break
    case "info":
      iconName = "info"
      iconColor = "#3b82f6"
      break
  }

  toast.innerHTML = `
        <div class="toast-icon">
            <i data-lucide="${iconName}" style="width: 1.25rem; height: 1.25rem; color: ${iconColor};"></i>
        </div>
        <div class="toast-content">${message}</div>
        <button class="toast-close" onclick="removeToast(this.parentElement)">
            <i data-lucide="x" style="width: 1rem; height: 1rem;"></i>
        </button>
    `

  toastContainer.appendChild(toast)
  lucide.createIcons()

  // Show toast with animation
  setTimeout(() => toast.classList.add("show"), 100)

  // Auto remove after duration
  setTimeout(() => removeToast(toast), duration)
}

function removeToast(toast) {
  toast.classList.remove("show")
  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast)
    }
  }, 300)
}

// Authentication
function checkAuth() {
  currentToken = localStorage.getItem("token")
  if (!currentToken) {
    window.location.href = "/login"
    return
  }
  loadCurrentView()
}

function logout() {
  localStorage.removeItem("token")
  window.location.href = "/login"
}

// View Management
function showAllBlogs() {
  currentView = "all"
  updateViewButtons()
  loadCurrentView()
}

function showMyBlogs() {
  currentView = "my"
  updateViewButtons()
  loadCurrentView()
}

function updateViewButtons() {
  const allBtn = document.getElementById("allBlogsBtn")
  const myBtn = document.getElementById("myBlogsBtn")

  if (currentView === "all") {
    allBtn.classList.add("btn-active")
    myBtn.classList.remove("btn-active")
  } else {
    allBtn.classList.remove("btn-active")
    myBtn.classList.add("btn-active")
  }
}

function loadCurrentView() {
  if (currentView === "all") {
    loadBlogs()
  } else {
    loadMyBlogs()
  }
}

// API Requests
async function makeAuthenticatedRequest(url, options = {}) {
  const headers = {
    Authorization: `Bearer ${currentToken}`,
    ...options.headers,
  }

  // Don't set Content-Type for FormData
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json"
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    localStorage.removeItem("token")
    window.location.href = "/login"
    return null
  }

  return response
}

// Blog Loading
async function loadBlogs() {
  try {
    document.getElementById("loadingSpinner").style.display = "block"
    document.getElementById("errorContainer").classList.add("hidden")
    document.getElementById("blogsContainer").innerHTML = ""

    const response = await makeAuthenticatedRequest("http://127.0.0.1:8000/landing/")

    if (!response || !response.ok) {
      throw new Error("Failed to load blogs")
    }

    const data = await response.json()
    displayBlogs(data.blogs, "All Blogs", false)
  } catch (error) {
    console.error("Error loading blogs:", error)
    document.getElementById("errorMessage").textContent = error.message
    document.getElementById("errorContainer").classList.remove("hidden")
    showToast("Failed to load blogs", "error")
  } finally {
    document.getElementById("loadingSpinner").style.display = "none"
  }
}

async function loadMyBlogs() {
  try {
    document.getElementById("loadingSpinner").style.display = "block"
    document.getElementById("errorContainer").classList.add("hidden")
    document.getElementById("blogsContainer").innerHTML = ""

    const response = await makeAuthenticatedRequest("http://127.0.0.1:8000/blogs/")

    if (!response || !response.ok) {
      throw new Error("Failed to load your blogs")
    }

    const data = await response.json()
    displayBlogs(data.blogs, "My Blogs", true)
  } catch (error) {
    console.error("Error loading my blogs:", error)
    document.getElementById("errorMessage").textContent = error.message
    document.getElementById("errorContainer").classList.remove("hidden")
    showToast("Failed to load your blogs", "error")
  } finally {
    document.getElementById("loadingSpinner").style.display = "none"
  }
}

// Blog Display
function displayBlogs(blogs, title, isMyBlogs) {
  const container = document.getElementById("blogsContainer")

  let html = ""

  // Add "Create New Blog" card for My Blogs view
  if (isMyBlogs) {
    html += `
            <div class="add-blog-section" onclick="openCreateBlogModal()">
                <i data-lucide="plus-circle" class="w-12 h-12 text-indigo-400 mx-auto mb-4"></i>
                <h3 class="text-lg font-semibold text-white mb-2">Create New Blog</h3>
                <p class="text-slate-400">Share your thoughts with the world</p>
            </div>
        `
  }

  if (blogs.length === 0 && !isMyBlogs) {
    html += `
            <div class="col-span-full text-center py-12">
                <i data-lucide="book-open" class="w-16 h-16 text-slate-600 mx-auto mb-4"></i>
                <p class="text-slate-400 text-lg">No blogs available in ${title}</p>
            </div>
        `
  } else if (blogs.length === 0 && isMyBlogs) {
    html += `
            <div class="col-span-full text-center py-12">
                <i data-lucide="edit" class="w-16 h-16 text-slate-600 mx-auto mb-4"></i>
                <p class="text-slate-400 text-lg">You haven't created any blogs yet</p>
                <p class="text-slate-500">Click the "Create New Blog" card to get started!</p>
            </div>
        `
  }

  html += blogs
    .map(
      (blog) => `
        <div class="blog-card p-6">
            ${
              blog.image_url
                ? `
                <div class="w-full h-48 mb-4 rounded-lg overflow-hidden bg-slate-800">
                    <img src="${blog.image_url}"
                         alt="${blog.title}"
                         class="w-full h-full object-cover blog-image"
                         crossorigin="anonymous"
                         onerror="handleImageError(this)"
                         onload="handleImageLoad(this)">
                </div>
            `
                : `
                <div class="w-full h-48 mb-4 image-placeholder">
                    <div class="text-center">
                        <span style="font-size: 2rem;">🖼️</span>
                        <p>No image</p>
                    </div>
                </div>
            `
            }
            
            <h3 class="text-xl font-bold text-white mb-3">${blog.title}</h3>
            <p class="text-slate-300 mb-4 line-clamp-3">${blog.content.substring(0, 150)}${blog.content.length > 150 ? "..." : ""}</p>
            
            <div class="flex flex-wrap gap-2 mb-4">
                <div class="stat-item">
                    <span style="color: #60a5fa; font-size: 1rem;">👁️</span>
                    <span class="text-slate-300 text-sm">${blog.read_count || 0}</span>
                </div>
                ${
                  !isMyBlogs
                    ? `
                    <div class="stat-item cursor-pointer" onclick="toggleLike(${blog.id})">
                        <span style="color: #4ade80; font-size: 1rem;">👍</span>
                        <span class="text-slate-300 text-sm">${blog.like_count || 0}</span>
                    </div>
                    <div class="stat-item cursor-pointer" onclick="toggleDislike(${blog.id})">
                        <span style="color: #f87171; font-size: 1rem;">👎</span>
                        <span class="text-slate-300 text-sm">${blog.dislike_count || 0}</span>
                    </div>
                `
                    : ""
                }
                <div class="stat-item">
                    <span style="color: #c084fc; font-size: 1rem;">💬</span>
                    <span class="text-slate-300 text-sm">${blog.feedback_count || 0}</span>
                </div>
            </div>
            
            <!-- Fixed button alignment -->
            <div class="blog-actions mb-4">
                ${
                  isMyBlogs
                    ? `
                    <button onclick="openEditBlogModal(${blog.id}, '${blog.title.replace(/'/g, "\\'")}', '${blog.content.replace(/'/g, "\\'")}', '${blog.image_url || ""}')" class="btn-success btn-sm">
                        <span>✏️</span>
                        Edit
                    </button>
                    <button onclick="deleteBlog(${blog.id})" class="btn-danger btn-sm">
                        <span>🗑️</span>
                    </button>
                `
                    : ""
                }
                <button onclick="openFeedbackModal(${blog.id})" class="btn-primary btn-sm">
                    <span>💬</span>
                    Feedback
                </button>
            </div>
            
            <div class="text-xs text-slate-500">
                Created: ${new Date(blog.created_at).toLocaleDateString()}
            </div>
        </div>
    `,
    )
    .join("")

  container.innerHTML = html
  lucide.createIcons()
}

// Blog Modal Management
function openCreateBlogModal() {
  editingBlogId = null
  document.getElementById("blogModalTitle").textContent = "Create New Blog"
  document.getElementById("blogSubmitText").textContent = "Create Blog"
  document.getElementById("blogForm").reset()
  clearImage()
  document.getElementById("blogModal").style.display = "block"
}

function openEditBlogModal(blogId, title, content, imageUrl) {
  editingBlogId = blogId
  document.getElementById("blogModalTitle").textContent = "Edit Blog"
  document.getElementById("blogSubmitText").textContent = "Update Blog"
  document.getElementById("blogTitle").value = title
  document.getElementById("blogContent").value = content

  // Show existing image if available
  if (imageUrl) {
    document.getElementById("imageUploadArea").classList.add("hidden")
    document.getElementById("imagePreview").classList.remove("hidden")
    document.getElementById("previewImg").src = imageUrl
    document.getElementById("imageName").textContent = "Current image"
  } else {
    clearImage()
  }

  document.getElementById("blogModal").style.display = "block"
}

function closeBlogModal() {
  document.getElementById("blogModal").style.display = "none"
  editingBlogId = null
}

// Image Handling
function handleImageSelect(input) {
  const file = input.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      document.getElementById("imageUploadArea").classList.add("hidden")
      document.getElementById("imagePreview").classList.remove("hidden")
      document.getElementById("previewImg").src = e.target.result
      document.getElementById("imageName").textContent = file.name
    }
    reader.readAsDataURL(file)
  }
}

function clearImage() {
  document.getElementById("blogImage").value = ""
  document.getElementById("imageUploadArea").classList.remove("hidden")
  document.getElementById("imagePreview").classList.add("hidden")
}

function setupDragAndDrop() {
  const fileInput = document.querySelector(".file-input")

  fileInput.addEventListener("dragover", (e) => {
    e.preventDefault()
    fileInput.classList.add("dragover")
  })

  fileInput.addEventListener("dragleave", () => {
    fileInput.classList.remove("dragover")
  })

  fileInput.addEventListener("drop", (e) => {
    e.preventDefault()
    fileInput.classList.remove("dragover")

    const files = e.dataTransfer.files
    if (files.length > 0) {
      document.getElementById("blogImage").files = files
      handleImageSelect(document.getElementById("blogImage"))
    }
  })
}

function handleImageError(img) {
  console.error("Failed to load image:", img.src)
  const placeholder = document.createElement("div")
  placeholder.className = "w-full h-full image-placeholder"
  placeholder.innerHTML = `
        <div class="text-center">
            <span style="font-size: 2rem;">❌</span>
            <p>Image failed to load</p>
        </div>
    `
  img.parentNode.replaceChild(placeholder, img)
}

function handleImageLoad(img) {
  img.classList.remove("loading")
}

// Blog Form Submission
document.getElementById("blogForm").addEventListener("submit", async (e) => {
  e.preventDefault()

  const submitBtn = document.getElementById("blogSubmitBtn")
  const submitText = document.getElementById("blogSubmitText")

  const originalText = submitText.textContent
  submitBtn.disabled = true
  submitText.textContent = editingBlogId ? "Updating..." : "Creating..."

  try {
    const formData = new FormData()
    formData.append("title", document.getElementById("blogTitle").value.trim())
    formData.append("content", document.getElementById("blogContent").value.trim())

    const imageFile = document.getElementById("blogImage").files[0]
    if (imageFile) {
      formData.append("image", imageFile)
    }

    const url = editingBlogId ? `http://127.0.0.1:8000/blogs/${editingBlogId}` : "http://127.0.0.1:8000/blogs/"

    const method = editingBlogId ? "PUT" : "POST"

    const response = await makeAuthenticatedRequest(url, {
      method: method,
      body: formData,
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")

      setTimeout(() => {
        closeBlogModal()
        loadMyBlogs() // Refresh the blogs list
      }, 1500)
    } else {
      const error = await response.json()
      throw new Error(error.detail || "Failed to save blog")
    }
  } catch (error) {
    console.error("Error saving blog:", error)
    showToast(error.message, "error")
  } finally {
    submitBtn.disabled = false
    submitText.textContent = originalText
  }
})

// Blog Actions
async function deleteBlog(blogId) {
  if (!confirm("Are you sure you want to delete this blog? This action cannot be undone.")) {
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/${blogId}/delete/`, {
      method: "PATCH",
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      loadMyBlogs() // Refresh the blogs list
    } else {
      const error = await response.json()
      throw new Error(error.detail || "Failed to delete blog")
    }
  } catch (error) {
    console.error("Error deleting blog:", error)
    showToast(error.message, "error")
  }
}

async function toggleLike(blogId) {
  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/${blogId}/like`, {
      method: "POST",
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      loadCurrentView() // Refresh to show updated counts
    }
  } catch (error) {
    console.error("Error toggling like:", error)
    showToast("Failed to update like", "error")
  }
}

async function toggleDislike(blogId) {
  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/${blogId}/dislike`, {
      method: "POST",
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      loadCurrentView() // Refresh to show updated counts
    }
  } catch (error) {
    console.error("Error toggling dislike:", error)
    showToast("Failed to update dislike", "error")
  }
}

// Feedback Management
async function openFeedbackModal(blogId) {
  currentBlogId = blogId
  document.getElementById("feedbackModal").style.display = "block"
  await loadFeedbacks(blogId)
}

function closeFeedbackModal() {
  document.getElementById("feedbackModal").style.display = "none"
  currentBlogId = null
  currentUserFeedback = null
}

async function loadFeedbacks(blogId) {
  try {
    const feedbackContent = document.getElementById("feedbackContent")
    feedbackContent.innerHTML = '<div class="text-center"><div class="loading mx-auto"></div></div>'

    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/${blogId}/feedbacks`)

    if (!response || !response.ok) {
      throw new Error("Failed to load feedbacks")
    }

    const feedbacks = await response.json()
    displayFeedbacks(feedbacks)
  } catch (error) {
    console.error("Error loading feedbacks:", error)
    document.getElementById("feedbackContent").innerHTML = `
            <div class="error-message">
                <p>Error loading feedbacks: ${error.message}</p>
                <button onclick="closeFeedbackModal()" class="btn-secondary mt-3">
                    ✕ Close
                </button>
            </div>
        `
    showToast("Failed to load feedbacks", "error")
  }
}

function displayFeedbacks(feedbacks) {
  const feedbackContent = document.getElementById("feedbackContent")
  currentUserFeedback = feedbacks.find((f) => f.is_current_user_feedback)

  let html = '<div class="space-y-4">'

  // Display existing feedbacks
  if (feedbacks.length > 0) {
    html += '<h3 class="text-lg font-semibold text-white mb-4">Feedbacks</h3>'
    feedbacks.forEach((feedback) => {
      html += `
                <div class="feedback-item ${feedback.is_current_user_feedback ? "border-indigo-500/50" : ""}">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-white">${feedback.username}</span>
                            ${feedback.is_current_user_feedback ? '<span class="text-xs bg-indigo-600 text-white px-2 py-1 rounded">You</span>' : ""}
                        </div>
                        <span class="text-xs text-slate-500">${new Date(feedback.created_at).toLocaleDateString()}</span>
                    </div>
                    <p class="text-slate-300 mb-2">${feedback.comment}</p>
                    ${
                      feedback.is_current_user_feedback
                        ? `
                        <div class="flex gap-2">
                            <button onclick="editFeedback(${feedback.id}, '${feedback.comment.replace(/'/g, "\\'")}')" class="btn-secondary text-xs">
                                ✏️ Edit
                            </button>
                            <button onclick="deleteFeedback(${feedback.id})" class="btn-secondary text-xs text-red-400">
                                🗑️ Delete
                            </button>
                        </div>
                    `
                        : ""
                    }
                </div>
            `
    })
  } else {
    html += '<p class="text-slate-400 text-center py-8">No feedbacks yet. Be the first to comment!</p>'
  }

  // Add feedback form
  if (!currentUserFeedback) {
    html += `
            <div class="feedback-form">
                <h4 class="text-white font-medium mb-3">Add Your Feedback</h4>
                <textarea id="newFeedbackText" class="form-input mb-3" rows="3" placeholder="Write your feedback here..."></textarea>
                <div class="flex gap-2">
                    <button onclick="createFeedback()" class="btn-primary">
                        📤 Submit Feedback
                    </button>
                    <button onclick="closeFeedbackModal()" class="btn-secondary">
                        ✕ Close
                    </button>
                </div>
            </div>
        `
  } else {
    // Add close button when user already has feedback
    html += `
            <div class="text-center mt-4">
                <button onclick="closeFeedbackModal()" class="btn-secondary">
                    ✕ Close
                </button>
            </div>
        `
  }

  html += "</div>"
  feedbackContent.innerHTML = html
}

async function createFeedback() {
  const comment = document.getElementById("newFeedbackText").value.trim()

  if (!comment) {
    showToast("Please enter a comment", "error")
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/${currentBlogId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      setTimeout(() => {
        loadFeedbacks(currentBlogId)
        loadCurrentView() // Refresh blog counts
      }, 1000)
    } else {
      const error = await response.json()
      throw new Error(error.detail || "Failed to create feedback")
    }
  } catch (error) {
    console.error("Error creating feedback:", error)
    showToast(error.message, "error")
  }
}

function editFeedback(feedbackId, currentComment) {
  const feedbackContent = document.getElementById("feedbackContent")
  feedbackContent.innerHTML = `
        <div class="feedback-form">
            <h4 class="text-white font-medium mb-3">Edit Your Feedback</h4>
            <textarea id="editFeedbackText" class="form-input mb-3" rows="3">${currentComment}</textarea>
            <div class="flex gap-2">
                <button onclick="updateFeedback(${feedbackId})" class="btn-primary">
                    💾 Update Feedback
                </button>
                <button onclick="loadFeedbacks(${currentBlogId})" class="btn-secondary">
                    Cancel
                </button>
                <button onclick="closeFeedbackModal()" class="btn-secondary">
                    ✕ Close
                </button>
            </div>
        </div>
    `
}

async function updateFeedback(feedbackId) {
  const comment = document.getElementById("editFeedbackText").value.trim()

  if (!comment) {
    showToast("Please enter a comment", "error")
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/feedback/${feedbackId}`, {
      method: "PUT",
      body: JSON.stringify({ comment }),
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      setTimeout(() => {
        loadFeedbacks(currentBlogId)
      }, 1000)
    } else {
      const error = await response.json()
      throw new Error(error.detail || "Failed to update feedback")
    }
  } catch (error) {
    console.error("Error updating feedback:", error)
    showToast(error.message, "error")
  }
}

async function deleteFeedback(feedbackId) {
  if (!confirm("Are you sure you want to delete this feedback?")) {
    return
  }

  try {
    const response = await makeAuthenticatedRequest(`http://127.0.0.1:8000/blogs/feedback/${feedbackId}`, {
      method: "DELETE",
    })

    if (response && response.ok) {
      const result = await response.json()
      showToast(result.message, "success")
      loadFeedbacks(currentBlogId)
      loadCurrentView() // Refresh blog counts
    } else {
      const error = await response.json()
      throw new Error(error.detail || "Failed to delete feedback")
    }
  } catch (error) {
    console.error("Error deleting feedback:", error)
    showToast(error.message, "error")
  }
}

// Modal Event Listeners
document.getElementById("feedbackModal").addEventListener("click", function (e) {
  if (e.target === this) {
    closeFeedbackModal()
  }
})

document.getElementById("blogModal").addEventListener("click", function (e) {
  if (e.target === this) {
    closeBlogModal()
  }
})
