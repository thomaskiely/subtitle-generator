import React, { useState } from "react";

const FileUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [font, setFont] = useState<string>("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
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
      const response = await fetch("http://localhost:8000/generate-subtitles", {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        console.error("Failed to upload file:", response.statusText);
        throw new Error("Error uploading file");
      }
  
      console.log("File uploaded successfully!");
  
      // Read the file as a blob (this will not consume the body stream again)
      const blob = await response.blob();
      console.log("Received file blob:", blob);
  
      // Create a URL for the blob and trigger a download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = selectedFile.name;
      a.click();
  
      // Clean up after download
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error during file upload:", error);
      alert("An error occurred. Please try again.");
    }
  };
  
  

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>
          Upload File:
          <input type="file" onChange={handleFileChange} />
        </label>
      </div>
      <div>
        <label>
          Font:
          <input
            type="text"
            value={font}
            onChange={handleFontChange}
            placeholder="Enter font name"
          />
        </label>
      </div>
      <button type="submit">Submit</button>
    </form>
  );
};

export default FileUploadForm;
