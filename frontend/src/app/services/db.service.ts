import { Injectable } from '@angular/core';
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface TravelWarningDB extends DBSchema {
    summaries: {
        key: string; // date
        value: any;
    };
    details: {
        key: string; // id
        value: any;
    };
}

@Injectable({
    providedIn: 'root',
})
export class DbService {
    private dbPromise: Promise<IDBPDatabase<TravelWarningDB>>;

    constructor() {
        this.dbPromise = openDB<TravelWarningDB>('travel-warning-db', 1, {
            upgrade(db) {
                db.createObjectStore('summaries');
                db.createObjectStore('details');
            },
        });
    }

    async getSummary(date: string): Promise<any> {
        return (await this.dbPromise).get('summaries', date);
    }

    async setSummary(date: string, data: any): Promise<void> {
        await (await this.dbPromise).put('summaries', data, date);
    }

    async getDetail(id: string): Promise<any> {
        return (await this.dbPromise).get('details', id);
    }

    async setDetail(id: string, data: any): Promise<void> {
        await (await this.dbPromise).put('details', data, id);
    }
}
