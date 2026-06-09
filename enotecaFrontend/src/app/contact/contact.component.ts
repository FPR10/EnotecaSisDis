import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import emailjs from '@emailjs/browser';

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
      'service_xskqjum',
      'template_lwymhtf',
      {
        name:    this.form.name,
        email:   this.form.email,
        subject: this.form.subject,
        message: this.form.message,
        time:    new Date().toLocaleTimeString('it-IT')
      },
      '6E7zw6qRiBTSL5z8W'
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
