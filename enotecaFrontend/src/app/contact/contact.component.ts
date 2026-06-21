import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import emailjs from '@emailjs/browser';

// Configurazione EmailJS (dashboard: https://dashboard.emailjs.com)
const EMAILJS_SERVICE_ID = 'service_n00520h';   // account email collegato (riceve i messaggi)
const EMAILJS_TEMPLATE_ID = 'template_lwymhtf'; // template con i placeholder name/email/subject/message/time
const EMAILJS_PUBLIC_KEY = '6E7zw6qRiBTSL5z8W'; // chiave pubblica dell'account EmailJS

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './contact.component.html',
  styleUrl: './contact.component.scss'
})
export class ContactComponent {

  form = { name: '', email: '', subject: '', message: '', time: '' };
  submitted = false;
  loading = false;

  constructor(private cdr: ChangeDetectorRef) {}

  onSubmit() {
    this.loading = true;

    emailjs.send(
      EMAILJS_SERVICE_ID,
      EMAILJS_TEMPLATE_ID,
      {
        name:    this.form.name,
        email:   this.form.email,
        subject: this.form.subject,
        message: this.form.message,
        time:    new Date().toLocaleTimeString('it-IT')
      },
      EMAILJS_PUBLIC_KEY
    )
      .then(() => {
        this.submitted = true;
        this.loading = false;
        this.cdr.detectChanges();
      })
      .catch(() => {
        alert('Errore durante l\'invio. Riprova più tardi.');
        this.loading = false;
        this.cdr.detectChanges();
      });
  }

  reset() {
    this.submitted = false;
    this.form = { name: '', email: '', subject: '', message: '', time: '' };
  }
}
