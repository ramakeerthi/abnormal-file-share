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