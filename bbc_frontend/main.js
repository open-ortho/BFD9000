function xrayUploader() {
  return {
      xrays: [],
      dragOver(event) {
          event.preventDefault();
          event.target.classList.add('dragging');
      },
      dragLeave(event) {
          event.preventDefault();
          event.target.classList.remove('dragging');
      },
      async drop(event) {
          event.preventDefault();
          event.target.classList.remove('dragging');

          this.xrays = [];
          const files = event.dataTransfer.files;
          const allowedTypes = ['image/png', 'image/jpeg', 'image/tiff'];

          for (let i = 0; i < files.length; i++) {
              if (allowedTypes.includes(files[i].type)) {
                  const formData = new FormData();
                  formData.append('image', files[i]);

                  const response = await fetch('http://localhost:8000/xray-info', {
                      method: 'POST',
                      body: formData
                  });

                  const data = await response.json();
                  this.xrays.push({
                      filename: URL.createObjectURL(files[i]),
                      xrayType: data.type_prediction,
                      rotation: data.rotation,
                      flip: data.flip
                  });
              }
          }
      }
  };
}
