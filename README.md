# secure-file-share
File sharing application developed as part of Abnormal Security Interview process.


# Process to run the application:

    git clone git@github.com:ramakeerthi/secure-file-share.git
    cd secure-file-share

    docker-compose up --build


# User Roles

The first user who registers in the application is automatically assigned the ADMIN role. All subsequent users who register will be assigned the GUEST role by default.

The admin user can manage other users' roles through the User Management tab in the navigation bar. In this tab, admins can:

- View all registered users (except themselves)
- Change any user's role between ADMIN and GUEST
- See each user's email and current role

Note: Admins cannot modify their own role to prevent accidentally removing admin access.

# Application Features

The application provides different tabs with the following features:

## File Upload Tab
- Upload files securely with client-side & server-side encryption
- Support for various file types and sizes
- Automatic encryption of files before storage

## File Manager Tab
- View all files you've uploaded
- Download your own files
- Delete files you own
- Share files with other users
- Set permissions for shared files (View Only/Download)

## Shared Files Tab
- Access files that other users have shared with you
- View or download shared files based on permissions
- See who shared the file
- Admins can view and download all uploaded files

## User Management Tab (Admin Only)
- View all registered users in the system
- Manage user roles (ADMIN/USER/GUEST)
- Monitor user accounts and their current roles

## Security Features
- Two-factor authentication (2FA) for enhanced security
- Client-side & Server-side encryption for file contents
- Secure file sharing with granular permissions
- HTTPS/SSL encryption for all communications