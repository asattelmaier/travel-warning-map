import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, of, BehaviorSubject } from 'rxjs';
import { map, switchMap, tap, catchError, finalize } from 'rxjs/operators';
import { TravelWarningSummary } from '../models/travel-warning';
import { environment } from '../../environments/environment';
import { DbService } from './db.service';

export interface SyncProgress {
  total: number;
  loaded: number;
  active: boolean;
}

@Injectable({ providedIn: 'root' })
export class TravelWarningService {
  private apiUrl = `${environment.travelWarningsApiBase}/travel-warnings`;
  private syncProgressSubject = new BehaviorSubject<SyncProgress>({ total: 0, loaded: 0, active: false });

  public syncProgress$ = this.syncProgressSubject.asObservable();

  constructor(private http: HttpClient, private db: DbService) { }

  private getTodayDate(): string {
    return new Date().toISOString().split('T')[0];
  }

  getWarnings(language: 'de' | 'en' = 'en', triggerSync: boolean = true): Observable<{ warnings: TravelWarningSummary[], effectiveDate: string }> {
    const today = this.getTodayDate();
    const cacheKey = `${language}_${today}`;

    // Only reset progress if we are actually triggering a sync
    if (triggerSync) {
      this.syncProgressSubject.next({ total: 0, loaded: 0, active: true });
    }

    // Network First Strategy
    return this.http.get<any>(`${this.apiUrl}?language=${language}`).pipe(
      map(resp => {
        const r = resp.response;
        const ids: string[] = r.contentList || [];
        const warnings = ids.map((id: string) => ({
          ...(r[id] as Omit<TravelWarningSummary, 'id'>),
          id
        }));
        return { warnings, effectiveDate: resp.effectiveDate };
      }),
      tap(data => {
        console.log(`[Cache] Network success. Updating summary for ${today}`);
        this.db.setSummary(cacheKey, data);
        if (triggerSync) {
          this.syncDetails(data.warnings, data.effectiveDate, language);
        }
      }),
      catchError(error => {
        console.log(`[Cache] Network failed. Falling back to DB for ${today}`, error);
        return from(this.db.getSummary(cacheKey)).pipe(
          map(cached => {
            if (cached) {
              console.log(`[Cache] Serving fallback summary for ${today} from DB`);
              if (triggerSync) {
                // If we are offline, sync will likely fail/skip, but we call it to ensure progress bar finishes
                this.syncDetails(cached.warnings, cached.effectiveDate, language);
              }
              return cached;
            }
            // No cache and no network
            throw error;
          })
        );
      })
    );
  }

  getWarningDetails(id: string, language: 'de' | 'en' = 'en'): Observable<any> {
    return from(this.db.getDetail(id)).pipe(
      switchMap(cached => {
        if (cached) {
          return of(cached);
        }
        return this.http.get<any>(`${this.apiUrl}/${id}?language=${language}`).pipe(
          tap(data => this.db.setDetail(id, data))
        );
      })
    );
  }

  getBackendCacheProgress(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/status/progress`);
  }

  private async syncDetails(warnings: TravelWarningSummary[], date: string, language: 'de' | 'en') {
    const total = warnings.length;
    let loaded = 0;

    console.log(`[Sync] Starting full sync for ${total} items...`);
    this.syncProgressSubject.next({ total, loaded: 0, active: true });

    // Process in chunks to avoid overwhelming the browser/network
    const chunks = this.chunkArray(warnings, 5);

    for (const chunk of chunks) {
      await Promise.all(chunk.map(async w => {
        const exists = await this.db.getDetail(w.id);
        if (!exists) {
          try {
            // Fetch from API
            const detail = await this.http.get<any>(`${this.apiUrl}/${w.id}?language=${language}`).toPromise();
            if (detail) {
              await this.db.setDetail(w.id, detail);
            }
          } catch (e) {
            console.error(`[Sync] Failed to load ${w.id}`, e);
          }
        }
        // Increment count whether we fetched it or it existed
        loaded++;
        this.syncProgressSubject.next({ total, loaded, active: true });
      }));
    }

    console.log(`[Sync] Complete.`);
    this.syncProgressSubject.next({ total, loaded: total, active: false });
  }

  private chunkArray(arr: any[], size: number) {
    const R = [];
    for (let i = 0; i < arr.length; i += size)
      R.push(arr.slice(i, i + size));
    return R;
  }
}
