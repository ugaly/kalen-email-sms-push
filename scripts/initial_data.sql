INSERT INTO notification_categories (name, description, priority, max_per_hour, max_per_day, primary_color, default_email_template, created_at) VALUES
('order_updates', 'Order status updates (placed, shipped, delivered)', 4, 50, 500, '#4CAF50', 'order_placed_email.html', NOW()),
('shipping', 'Shipping and delivery notifications', 4, 50, 500, '#2196F3', 'order_shipped_email.html', NOW()),
('marketing', 'Marketing and promotional messages', 1, 10, 100, '#FF9800', 'marketing_email.html', NOW()),
('security', 'Security alerts and notifications', 4, 20, 200, '#F44336', 'security_alert_email.html', NOW()),
('system', 'System maintenance and updates', 2, 5, 50, '#673AB7', 'base_email_template.html', NOW()),
('reminders', 'Appointment and task reminders', 2, 30, 300, '#009688', 'base_email_template.html', NOW());


INSERT INTO notification_templates (name, template_type, subject, content, html_template, use_html_template, primary_color, variables, is_active, created_at, updated_at) VALUES
('order_placed_email', 'email', 'Order Confirmation - #{{order_number}}', 
 'Hi {{customer_name}},\n\nYour order #{{order_number}} has been placed successfully.\n\nOrder Details:\n{{order_details}}\n\nThank you for your purchase!', 
 'order_placed_email.html', true, '#4CAF50',
 '{"order_number": "string", "customer_name": "string", "order_date": "string", "order_items": "array", "order_total": "string"}', 
 true, NOW(), NOW()),

('order_shipped_email', 'email', 'Your Order Has Shipped - #{{order_number}}', 
 'Hi {{customer_name}},\n\nGreat news! Your order #{{order_number}} has been shipped.\n\nTracking Number: {{tracking_number}}\n\nExpected Delivery: {{delivery_date}}', 
 'order_shipped_email.html', true, '#2196F3',
 '{"order_number": "string", "customer_name": "string", "tracking_number": "string", "carrier": "string", "ship_date": "string", "delivery_date": "string", "shipping_address": "string"}', 
 true, NOW(), NOW()),

('order_delivered_email', 'email', 'Order Delivered - #{{order_number}}', 
 'Hi {{customer_name}},\n\nYour order #{{order_number}} has been
