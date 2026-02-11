# Animal Detection System

A complete IoT-based animal detection and monitoring system integrating Raspberry Pi hardware, cloud storage, AI-powered detection, and SMS alerts.

## Overview

This system uses PIR motion sensors to detect animal movement, captures images with a camera module, processes them using deep learning models in Google Colab, and sends real-time SMS alerts to farmers or property owners.

## Features

- **Real-time Motion Detection**: PIR sensor triggers immediate LED activation and image capture
- **Cloud Storage**: Images stored in Supabase Storage and ThingSpeak
- **AI-Powered Detection**: Google Colab integration for animal identification
- **SMS Alerts**: Instant notifications via Twilio or Fast2SMS
- **Web Dashboard**: Beautiful interface to view captured and labeled images
- **User Authentication**: Secure login and signup system
- **Multi-user Support**: Each user has their own monitoring space
- **Hardware Simulation**: Test the complete workflow without physical hardware

## System Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│   + PIR Sensor  │
│   + Camera      │
│   + LED/Buzzer  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase      │
│  Edge Function  │
│  (upload-image) │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌──────────────┐
│ Storage │ │ ThingSpeak   │
└─────────┘ └──────────────┘
     │
     ▼
┌─────────────────┐
│ Google Colab    │
│   AI Model      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase      │
│  Edge Function  │
│(process-detect) │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌──────────────┐
│Dashboard│ │ SMS Service  │
└─────────┘ └──────────────┘
```

## Technology Stack

### Frontend
- React 18 with TypeScript
- Tailwind CSS for styling
- Vite for build tooling
- Lucide React for icons

### Backend
- Supabase (PostgreSQL database)
- Supabase Edge Functions (Deno)
- Supabase Storage (image hosting)
- Row Level Security (RLS)

### Hardware
- Raspberry Pi 3B+
- PIR Motion Sensor
- Camera Module
- LED and Buzzer

### AI/ML
- Google Colab (Python environment)
- TensorFlow/Keras
- MobileNetV2 or custom trained models

### Integrations
- ThingSpeak (cloud data storage)
- Twilio (SMS notifications)
- Fast2SMS (alternative SMS service)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Supabase account
- (Optional) Raspberry Pi 3B+ with hardware components
- (Optional) Google Colab account
- (Optional) ThingSpeak account
- (Optional) Twilio or Fast2SMS account

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd animal-detection-system
```

2. **Install dependencies**

```bash
npm install
```

3. **Configure environment variables**

The `.env` file should already contain your Supabase credentials:

```env
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-anon-key
```

4. **Start the development server**

```bash
npm run dev
```

5. **Build for production**

```bash
npm run build
```

## Database Setup

The database schema is automatically created using Supabase migrations. The system includes:

- `captured_images` - Raw images from Raspberry Pi
- `labeled_images` - AI-processed images with animal labels
- `user_settings` - User configuration for integrations
- Storage buckets for `captured-images` and `labeled-images`

### Creating Storage Buckets

You need to manually create two storage buckets in Supabase:

1. Go to Storage in your Supabase dashboard
2. Create bucket: `captured-images` (Public)
3. Create bucket: `labeled-images` (Public)

## Configuration Guide

### 1. Web Dashboard

1. Open the application in your browser
2. Sign up for a new account
3. Login with your credentials
4. Navigate to Settings
5. Configure your API keys:
   - ThingSpeak API Key and Channel ID
   - Google Colab Webhook URL
   - SMS service credentials

### 2. Raspberry Pi Setup

Follow the detailed guide in `docs/RASPBERRY_PI_SETUP.md`:

1. Connect hardware components
2. Install Python dependencies
3. Configure the Python script with your user ID
4. Run the monitoring script

### 3. Google Colab Setup

Follow the detailed guide in `docs/GOOGLE_COLAB_SETUP.md`:

1. Create a new Colab notebook
2. Set up ngrok for public URL
3. Load or train your AI model
4. Run the webhook server
5. Copy the webhook URL to Settings

### 4. ThingSpeak Setup

1. Create a free ThingSpeak account
2. Create a new channel
3. Add fields for your data
4. Copy Write API Key and Channel ID
5. Enter in Settings page

### 5. SMS Setup

#### For Twilio:
1. Sign up at [twilio.com](https://twilio.com)
2. Get Account SID and Auth Token
3. Get a Twilio phone number
4. Enter credentials in Settings

#### For Fast2SMS:
1. Sign up at [fast2sms.com](https://fast2sms.com)
2. Get your API key
3. Enter in Settings

## Usage

### Testing Without Hardware

1. Login to the dashboard
2. Click "Show Upload" in the simulation section
3. Upload an animal image
4. View the image in "Captured Images" tab
5. (If Colab is configured) Check "Labeled Images" for AI results

### With Raspberry Pi Hardware

1. Set up hardware according to guide
2. Run the Python script on Raspberry Pi
3. PIR sensor detects motion
4. LED turns on immediately
5. Image is captured and uploaded
6. After 2 minutes, buzzer sounds
7. View results in dashboard
8. (If configured) Receive SMS alert

## API Documentation

Complete API documentation is available in `docs/API_DOCUMENTATION.md`:

- Upload Image endpoint
- Process Detection endpoint
- Database schema
- Webhook formats
- Error codes

## Project Structure

```
animal-detection-system/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx      # Main dashboard UI
│   │   ├── Login.tsx          # Login page
│   │   ├── Signup.tsx         # Signup page
│   │   └── Settings.tsx       # Settings/configuration
│   ├── contexts/
│   │   └── AuthContext.tsx    # Authentication state
│   ├── lib/
│   │   └── supabase.ts        # Supabase client setup
│   ├── App.tsx                # Main app component
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── docs/
│   ├── API_DOCUMENTATION.md   # API reference
│   ├── GOOGLE_COLAB_SETUP.md  # Colab integration guide
│   └── RASPBERRY_PI_SETUP.md  # Hardware setup guide
├── supabase/
│   └── functions/             # Edge functions
│       ├── upload-image/      # Image upload handler
│       └── process-detection/ # AI results handler
└── package.json
```

## Security Features

- Row Level Security (RLS) on all database tables
- Secure authentication with Supabase Auth
- API keys stored securely in user settings
- No sensitive data exposed in client code
- CORS protection on edge functions

## Workflow

1. **Motion Detected** → PIR sensor triggers
2. **LED Activation** → Visual indicator turns on
3. **Image Capture** → Camera takes photo
4. **Upload to Cloud** → Image sent to Supabase
5. **ThingSpeak Backup** → (Optional) Stored in ThingSpeak
6. **AI Processing** → Google Colab analyzes image
7. **Animal Identified** → Model returns label and confidence
8. **Results Saved** → Labeled image stored in database
9. **SMS Alert** → (Optional) User receives notification
10. **Buzzer Sounds** → After 2 minutes, animal is scared away
11. **Dashboard Update** → User views results in web interface

## Troubleshooting

### Common Issues

**Images not appearing in dashboard:**
- Check if storage buckets are created and public
- Verify user is logged in
- Check browser console for errors

**Raspberry Pi not uploading:**
- Verify internet connection
- Check API URL configuration
- Ensure user ID is correct

**Colab webhook not working:**
- Verify ngrok URL is correctly copied to Settings
- Check if Colab cell is still running
- Test webhook with /health endpoint

**SMS not sending:**
- Verify API credentials are correct
- Check phone number format
- Ensure SMS service has credits

## Performance

- Image upload: ~2-5 seconds
- AI processing: ~5-10 seconds
- Total detection time: ~10-20 seconds
- Dashboard load time: <2 seconds

## Limitations

- Free Colab sessions timeout after 12 hours
- ngrok URL changes on Colab restart
- ThingSpeak free tier: 3 million messages/year
- Supabase free tier: 500MB database, 1GB storage
- SMS costs vary by provider

## Future Enhancements

- [ ] Real-time notifications using WebSockets
- [ ] Mobile app for iOS and Android
- [ ] Video recording capability
- [ ] Multiple camera support
- [ ] Advanced analytics and reports
- [ ] Integration with home automation systems
- [ ] Support for more SMS providers
- [ ] Offline mode with local processing
- [ ] GPS location tracking
- [ ] Weather integration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use this project for educational or commercial purposes.

## Support

For questions or issues:
- Check the documentation in `/docs`
- Review the API documentation
- Check Supabase logs for errors
- Verify all credentials are correct

## Credits

Built with:
- [Supabase](https://supabase.com) - Backend and database
- [React](https://react.dev) - Frontend framework
- [Tailwind CSS](https://tailwindcss.com) - Styling
- [Lucide](https://lucide.dev) - Icons
- [TensorFlow](https://tensorflow.org) - Machine learning
- [Raspberry Pi](https://raspberrypi.org) - Hardware platform

---

**Happy Monitoring!**
"# iot_animal_detection" 
