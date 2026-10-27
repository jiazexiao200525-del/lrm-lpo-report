(() => {
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const caption = document.getElementById('lightbox-caption');
  const close = () => {
    lightbox.classList.remove('open');
    lightbox.setAttribute('aria-hidden', 'true');
    lightboxImg.removeAttribute('src');
    document.body.style.overflow = '';
  };
  document.querySelectorAll('.image-button').forEach((button) => {
    button.addEventListener('click', () => {
      lightboxImg.src = button.dataset.src;
      lightboxImg.alt = button.querySelector('img')?.alt || '';
      caption.textContent = button.dataset.caption || '';
      lightbox.classList.add('open');
      lightbox.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    });
  });
  document.querySelector('.lightbox-close').addEventListener('click', close);
  lightbox.addEventListener('click', (event) => { if (event.target === lightbox) close(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && lightbox.classList.contains('open')) close(); });
})();
