const BASE_URL = window.BASE_URL || '';
let currentPage = 1;
let isLoading = false;

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    if (document.body) {
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 100);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

async function makeAuthenticatedRequest(url, options = {}) {
    try {
        let response = await fetch(url, {
            ...options,
            credentials: 'include'
        });

        if (response.status === 401) {
            console.log('Access token expired, trying to refresh...');
            
            const refreshResponse = await fetch(`${BASE_URL}/api/refresh/`, {
                method: 'POST',
                credentials: 'include'
            });

            if (refreshResponse.ok) {
                console.log('Token refreshed successfully, retrying original request...');
                response = await fetch(url, {
                    ...options,
                    credentials: 'include'
                });
            } else {
                console.log('Refresh failed, redirecting to login...');
                showNotification('Session expired. Please login again.', 'error');
                setTimeout(() => {
                    window.location.href = `${BASE_URL}/user/login/`;
                }, 1500);
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// Blog loading function
async function loadBlogs(page = 1) {
    if (isLoading) return;
    isLoading = true;

    try {
        const response = await makeAuthenticatedRequest(`${BASE_URL}/api/landing/?page=${page}&page_size=10`);
        
        if (!response) return;

        if (response.ok) {
            const data = await response.json();
            if (typeof window.displayBlogs === 'function') {
                window.displayBlogs(data.blogs.blogs);
            }
            if (typeof window.updatePagination === 'function') {
                window.updatePagination(data.blogs.page, Math.ceil(data.blogs.blogs.length / 10));
            }
            currentPage = page;
        } else {
            const errorData = await response.json();
            showNotification(errorData.detail || 'Failed to load blogs', 'error');
        }
    } catch (error) {
        console.error('Error loading blogs:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        isLoading = false;
    }
}

// Like/Dislike functions
async function toggleLike(blogId, button) {
    try {
        const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${blogId}/like`, {
            method: 'POST'
        });

        if (!response) return;

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            
            const likeCount = parseInt(button.textContent.match(/\d+/)[0]);
            const isLiked = button.classList.contains('liked');
            
            if (isLiked) {
                button.classList.remove('liked');
                button.innerHTML = `👍 ${likeCount - 1}`;
            } else {
                button.classList.add('liked');
                button.innerHTML = `👍 ${likeCount + 1}`;
                
                const dislikeBtn = button.nextElementSibling;
                if (dislikeBtn && dislikeBtn.classList.contains('disliked')) {
                    dislikeBtn.classList.remove('disliked');
                    const dislikeCount = parseInt(dislikeBtn.textContent.match(/\d+/)[0]);
                    dislikeBtn.innerHTML = `👎 ${dislikeCount - 1}`;
                }
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to like blog', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    }
}

async function toggleDislike(blogId, button) {
    try {
        const response = await makeAuthenticatedRequest(`${BASE_URL}/api/blogs/${blogId}/dislike`, {
            method: 'POST'
        });

        if (!response) return;

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            
            const dislikeCount = parseInt(button.textContent.match(/\d+/)[0]);
            const isDisliked = button.classList.contains('disliked');
            
            if (isDisliked) {
                button.classList.remove('disliked');
                button.innerHTML = `👎 ${dislikeCount - 1}`;
            } else {
                button.classList.add('disliked');
                button.innerHTML = `👎 ${dislikeCount + 1}`;
                
                const likeBtn = button.previousElementSibling;
                if (likeBtn && likeBtn.classList.contains('liked')) {
                    likeBtn.classList.remove('liked');
                    const likeCount = parseInt(likeBtn.textContent.match(/\d+/)[0]);
                    likeBtn.innerHTML = `👍 ${likeCount - 1}`;
                }
            }
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Failed to dislike blog', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    }
}

// Navigation functions
function viewBlog(blogId) {
    window.location.href = `${BASE_URL}/user/blog-detail/?id=${blogId}`;
}

function goToMyBlogs() {
    window.location.href = `${BASE_URL}/user/my-blog/`;
}

// Logout function
async function logout() {
    try {
        const response = await fetch(`${BASE_URL}/api/logout/`, {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            showNotification('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = `${BASE_URL}/user/login/`;
            }, 1000);
        } else {
            showNotification('Logout failed', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    }
}

window.loadBlogs = loadBlogs;
window.toggleLike = toggleLike;
window.toggleDislike = toggleDislike;
window.viewBlog = viewBlog;
window.goToMyBlogs = goToMyBlogs;
window.logout = logout;

window.addEventListener('load', () => {
    loadBlogs(1);
});

