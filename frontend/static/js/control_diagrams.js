// Wait until DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const imgElement = document.getElementById('controlImage');

    document.querySelectorAll('a[data-img]').forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            const filename = event.target.getAttribute('data-img');
            imgElement.src = `${filename}`;
        });
    });
});