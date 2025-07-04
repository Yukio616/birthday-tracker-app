document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.querySelector('input[name="profile"]');
  if (fileInput) {
    fileInput.addEventListener('change', () => {
      const img = document.querySelector('.avatar');
      if (fileInput.files && fileInput.files[0]) {
        img.src = URL.createObjectURL(fileInput.files[0]);
      }
    });
  }
});
