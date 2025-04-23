export interface TravelWarningsGeoJson {
  type: 'FeatureCollection';
  features: TravelWarningFeature[];
}

export interface TravelWarningFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: any;
  };
  properties: {
    uid: string;
    countryName: string;
    severity: number;
    severityDescription: string;
    validFrom: string;
    validTo?: string;
    lastUpdated: string;
    [key: string]: any;
  };
}
// Summarized Warning data for country lookup
export interface TravelWarningSummary {
  id: string;
  title: string;
  countryCode: string;
  iso3CountryCode: string;
  countryName: string;
  warning: boolean;
  partialWarning: boolean;
  situationWarning: boolean;
  situationPartWarning: boolean;
  lastModified: number;
  effective: number;
}