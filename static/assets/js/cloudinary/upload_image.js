const cloudName = "canallcc";
const uploadPreset = "ml_default";

const myWidget = cloudinary.createUploadWidget(
  {
    cloudName: cloudName,
    uploadPreset: uploadPreset,
    sources: [
      "local",
      "url"
    ],
    googleApiKey: "<image_search_google_api_key>",
    showAdvancedOptions: false,
    cropping: false,
    multiple: true,
    defaultSource: "local",
    styles: {
      palette: {
        window: "#ffffff",
        sourceBg: "#f4f4f5",
        windowBorder: "#90a0b3",
        tabIcon: "#000000",
        inactiveTabIcon: "#555a5f",
        menuIcons: "#555a5f",
        link: "#0433ff",
        action: "#339933",
        inProgress: "#0433ff",
        complete: "#339933",
        error: "#cc0000",
        textDark: "#000000",
        textLight: "#fcfffd"
      },
      fonts: {
        default: null,
        "sans-serif": {
          url: null,
          active: true
        }
      }
    }
  },
  (error, result) => {
    if (!error && result && result.event === "success") {
      document.getElementById("uploadedimage").setAttribute("src", result.info.secure_url);
    }
  }
);

document.getElementById("upload_widget").addEventListener(
  "click",
  function () {
    window.alert("Pulsado");
    myWidget.open();
  },
  false
);