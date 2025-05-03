import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TravelWarningSummary } from '../models/travel-warning';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class TravelWarningService {
  // Proxy prefix /api, endpoint is /travel-warnings
  private apiUrl = `${environment.travelWarningsApiBase}/travel-warnings`;

  constructor(private http: HttpClient) {}

  /**
   * Fetch the latest travel warning summaries (defaults to English)
   */
  getWarnings(language: 'de' | 'en' = 'en'): Observable<TravelWarningSummary[]> {
    return this.http
      .get<any>(`${this.apiUrl}?language=${language}`)
      .pipe(
        map(resp => {
          const r = resp.response;
          const ids: string[] = r.contentList;
          return ids.map((id: string) => ({
            // Spread all summary fields except 'id', then assign 'id' explicitly
            ...(r[id] as Omit<TravelWarningSummary, 'id'>),
            id
          }));
        })
      );
  }

  /**
   * Fetch detailed travel warning information for a specific country
   */
  getWarningDetails(id: string, language: 'de' | 'en' = 'en'): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}?language=${language}`);
  }
}
