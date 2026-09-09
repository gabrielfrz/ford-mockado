import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
/** Request export files and trigger browser downloads. */
export class ExtractButtonService {
  constructor(private http: HttpClient) {}

  /**
    * Request a downloadable file from an API endpoint.
    * @param endpointUrl API URL without a query string.
    * @param params Query parameters, such as `{ gi_id: '123' }`.
    * @returns An observable containing the file blob.
   */
  downloadFile(endpointUrl: string, params: Record<string, any>): Observable<Blob> {
    // Build the complete URL from the supplied query parameters.
    const queryString = new URLSearchParams();
    Object.keys(params).forEach(key => {
      queryString.append(key, params[key]);
    });

    const fullUrl = `${endpointUrl}?${queryString.toString()}`;

    return this.http.get(fullUrl, {
      responseType: 'blob'
    });
  }

  /**
    * Trigger a browser download for an in-memory blob.
    * @param blob File content to download.
    * @param fileName File name presented to the user.
   */
  triggerDownload(blob: Blob, fileName: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
}
