import React, { useState } from "react";
import './App.css';

const App = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [font, setFont] = useState<string>("");
  const [downloadLink, setDownloadLink] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFontChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFont(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!selectedFile || !font) {
      alert("Please provide both a file and a font.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("font", font);

    try {
      const response = await fetch("http://127.0.0.1:8000/generate-subtitles", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        console.error("Failed to upload file:", response.statusText);
        throw new Error("Error uploading file");
      }

      // Read the file as a blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      // Set the download link
      setDownloadLink(url);
    } catch (error) {
      console.error("Error during file upload:", error);
      alert("An error occurred. Please try again.");
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <h2>Upload Subtitle File</h2>
        <input
          type="file"
          onChange={handleFileChange}
          accept=".mp4, .mkv, .avi"
        />
        <input
          type="text"
          value={font}
          onChange={handleFontChange}
          placeholder="Enter font name"
        />
        <button type="submit">Upload</button>

        {/* Show the download button if the file is ready */}
        {downloadLink && (
          <div>
            <a href={downloadLink} download="generated.mp4">
              <button type="button">Download Processed File</button>
            </a>
          </div>
        )}
      </form>
    </div>
  );
};

export default App;

