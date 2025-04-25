import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { provideHttpClient } from '@angular/common/http';
import { TravelWarningService } from './app/services/travel-warning.service';

bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(),
    TravelWarningService
  ]
}).catch(err => console.error(err));
