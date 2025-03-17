import React, { useState } from "react";
import './App.css';

const ffmpegFonts = [
  "Arial", "Verdana", "Times New Roman", "Courier New", "Georgia", 
  "Trebuchet MS", "Impact", "Comic Sans MS", "Lucida Console", "Tahoma"
];

const App = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [font, setFont] = useState<string>('Comic Sans MS');
  const [fontSize, setFontSize] = useState<string>('');
  const [bold, setBold] = useState<string>('False');
  const [alignment, setAlignment] = useState<string>('Bottom');
  const [fontColor, setFontColor] = useState<string>('#ffffff');
  const [useOutline, setUseOutline] = useState<string>('False');
  const [outlineColor, setOutlineColor] = useState<string>('#ffffff');
  const [downloadLink, setDownloadLink] = useState<string | null>(null);
  const [showDownload, setShowDownload] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setErrorMessage("");
    }
  };

  const handleFontChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setFont(event.target.value);
  };

  const handleFontColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFontColor(event.target.value);
  };

  const handleOutlineColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setOutlineColor(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setShowDownload(false);
    if (!selectedFile) {
      setErrorMessage("Please upload an mp4 file.");
      return;
    }

    setIsLoading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("font_style", font);
    formData.append("font_size", fontSize);
    formData.append("bold", bold);
    formData.append("alignment", alignment);
    formData.append("primary_color", fontColor.slice(1))

    if(useOutline==='True'){
      formData.append("outline_color", outlineColor.slice(1));
    }

    const subtitleEndpoint = import.meta.env.VITE_SUBTITLE_ENDPOINT;

    try {
      const response = await fetch(`${subtitleEndpoint}`, {
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

      // Set the download link and show the button
      setDownloadLink(url);
      setShowDownload(true);
    } catch (error) {
      console.error("Error during file upload:", error);
      setErrorMessage("Please upload an mp4 file.");
      return;
    } finally{
      setIsLoading(false)
    }
  };

  const handleDownload = () => {
    setShowDownload(false);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <h2>Subtitle Generator</h2>

        {/* File Upload Section */}
        <div className="form-group">
          <label htmlFor="file-upload">
            Choose a file <span className="required">*</span>
          </label>
          <input
            id="file-upload"
            type="file"
            onChange={handleFileChange}
            accept=".mp4"
          />
        </div>

        {/* Font Selection Section */}
        <div className="form-group">
          <label htmlFor="font-select">Font Style</label>
          <select id="font-select" value={font} onChange={handleFontChange}>
            {ffmpegFonts.map((fontName) => (
              <option key={fontName} value={fontName}>
                {fontName}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="font-size">Font Size</label>
          <input 
            type="text" 
            id="font-size" 
            value={fontSize} 
            onChange={(e) => setFontSize(e.target.value)} 
            placeholder="Enter font size" 
          />
          </div>
        
          <div className="form-group">
            <label htmlFor="bold">Bold</label>
            <select value={bold} onChange={(e) => setBold(e.target.value)}>
              <option value="False">False</option>
              <option value="True">True</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="alignment">Alignment</label>
            <select value={alignment} onChange={(e) => setAlignment(e.target.value)}>
              <option value="Top">Top</option>
              <option value="Bottom">Bottom</option>
              <option value="Center">Center</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="font-color">Font Color</label>
            <input 
              type="color" 
              id="font-color" 
              value={fontColor} 
              onChange={handleFontColorChange}
            />
          </div>
          

          <div className="form-group">
            <label htmlFor="use-outline">Use Outline</label>
            <select value={useOutline} onChange={(e) => setUseOutline(e.target.value)}>
              <option value="False">False</option>
              <option value="True">True</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="outline-color">Outline Color</label>
            <input 
              type="color" 
              id="font-color" 
              value={outlineColor} 
              onChange={handleOutlineColorChange} 
            />
          </div>

        <button type="submit">Upload</button>

        {isLoading && (
          <div className="spinner-container">
            <div className="spinner"></div>
          </div>
        )}

        {/* Error Message */}
        {errorMessage && <p className="error-message">{errorMessage}</p>}

        {/* Show the download button if the file is ready */}
        {downloadLink && showDownload && (
          <div className="download-button">
            <a href={downloadLink} download="generated.mp4">
              <button type="button" onClick={handleDownload}>
                Download Processed File
              </button>
            </a>
          </div>
        )}
      </form>
    </div>
  );
};

export default App;
