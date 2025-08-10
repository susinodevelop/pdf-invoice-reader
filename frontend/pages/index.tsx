import { useState } from 'react';

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [response, setResponse] = useState<any>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [advisor, setAdvisor] = useState('');
  const [forceOCR, setForceOCR] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(event.target.files);
  };

  const handleSubmit = async () => {
    if (!files) return;
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    formData.append('advisor', advisor);
    formData.append('force_ocr', String(forceOCR));
    try {
      setStatus('loading');
      const res = await fetch('http://localhost:8080/api/invoices/process-pdf', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setResponse(data);
      setStatus('done');
    } catch (error) {
      setStatus('error');
    }
  };

  return (
    <main style={{ padding: '2rem' }}>
      <h1>PDF Invoice Reader</h1>
      <div>
        <label>
          Advisor:
          <input type="text" value={advisor} onChange={(e) => setAdvisor(e.target.value)} />
        </label>
      </div>
      <div>
        <label>
          Force OCR:
          <input type="checkbox" checked={forceOCR} onChange={(e) => setForceOCR(e.target.checked)} />
        </label>
      </div>
      <div>
        <input type="file" multiple accept="application/pdf" onChange={handleFileChange} />
      </div>
      <button onClick={handleSubmit}>Process PDFs</button>
      {status === 'loading' && <p>Processing...</p>}
      {response && (
        <div>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}
