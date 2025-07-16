describe('User Permissions', () => {
    beforeEach(async () => {
        // Login as test user
        await page.goto('/login');
        await page.fill('#email', 'admin@example.com');
        await page.fill('#password', 'admin123');
        await page.click('#login-button');
    });

    it('should show admin panel for admin users', async () => {
        await page.goto('/admin');
        expect(await page.isVisible('#admin-dashboard')).toBe(true);
    });

    it('should manage user roles', async () => {
        await page.goto('/admin/users');
        await page.click('#add-role-button');
        await page.fill('#role-name', 'editor');
        await page.click('#save-role');
        expect(await page.isVisible('#role-saved-message')).toBe(true);
    });
}); 