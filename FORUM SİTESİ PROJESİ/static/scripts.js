function likeComment(commentId) {
    fetch(`/like/${commentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.likes) {
            document.getElementById(`like-count-${commentId}`).textContent = data.likes;
        }
    })
    .catch(error => console.error('Error:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    // Yorum Beğenme işlevi
    const likeBtns = document.querySelectorAll('.like-btn');
    likeBtns.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.getAttribute('data-comment-id');
            likeComment(commentId);
        });
    });
});
