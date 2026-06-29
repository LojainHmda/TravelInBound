# TravelBookPro - UI Design Guide

## 🎨 Color Palette

### Primary Colors
```css
--primary-color: #223A5E;      /* Custom Dark Blue - Main brand color */
--secondary-color: #efdea4;    /* Beige/Cream */
--button-color: #efdea4;       /* Beige - Main button color */
--navy-blue: #223A5E;          /* Navy Blue for headers/sidebar */
```

### Accent Colors (Yellow/Gold Theme)
```css
#FFBF00    /* Primary Yellow/Gold - Main accent */
#FFD700    /* Gold - Bright highlights */
#FFA500    /* Orange - Action elements */
#FFB347    /* Light Orange */
#FFED4E    /* Light Yellow - Hover states */
```

### Background Colors
```css
--background-color: #ffffff;           /* White - Main background */
--dashboard-bg-color: #f0f0f0;        /* Light Gray - Dashboard bg */
--light-color: #ffffff;               /* White */
```

### Text Colors
```css
--text-dark: #223A5E;                 /* Dark Blue - Main text */
--text-light: #f8f9fa;                /* Light text */
--dashboard-text-color: #223A5E;      /* Dashboard text */
```

### Status Colors
```css
--status-request: #efdea4;            /* Beige - Request status */
--status-invoice: #efdea4;            /* Beige - Invoice status */
--status-in-progress: #efdea4;        /* Beige - In Progress */
--status-completed: #efdea4;          /* Beige - Completed */
```

---

## 🌈 Gradient Styles

### Primary Action Gradients (Yellow/Gold)
```css
/* Main Button Gradient */
background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);

/* Hover State */
background: linear-gradient(135deg, #FFED4E 0%, #FFB347 100%);

/* Card/Stat Gradients */
background: linear-gradient(135deg, #FFD700, #FFA500);
box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
```

### Purple/Blue Gradients (Secondary Actions)
```css
/* Purple Gradient - Premium/Final Status */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Alternative Purple */
background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%);
```

### Status Flow Gradients
```css
/* REQUEST / IN_PROGRESS - Orange Gradient */
background: linear-gradient(135deg, #FF8C00 0%, #FFB347 50%, #FFBF00 100%);
color: #1a202c;
border: 4px solid #FF8C00;
box-shadow: 
    0 10px 30px rgba(255, 140, 0, 0.4),
    0 0 0 10px rgba(255, 140, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);

/* CONFIRMED - Green Gradient */
background: linear-gradient(135deg, #10b981 0%, #34d399 50%, #6ee7b7 100%);
color: white;
border: 4px solid #10b981;
box-shadow: 
    0 10px 30px rgba(16, 185, 129, 0.4),
    0 0 0 10px rgba(16, 185, 129, 0.1);

/* COMPLETED - Purple Gradient */
background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #c084fc 100%);
color: white;
border: 4px solid #7c3aed;
```

### Background Gradients
```css
/* Light Gradient - Cards/Panels */
background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);

/* Subtle Card Background */
background: linear-gradient(145deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
```

---

## 🎯 Button Styles

### Primary Button (Yellow/Gold)
```css
.btn-primary {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: #333;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(255, 165, 0, 0.3);
    transition: all 0.3s ease;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #FFED4E 0%, #FFB347 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(255, 165, 0, 0.4);
}
```

### Secondary Button (Purple)
```css
.btn-secondary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-secondary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.5);
}
```

### Icon Buttons
```css
.btn-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #e9ecef;
    background: white;
    transition: all 0.3s;
}

.btn-icon:hover {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    border-color: #FFA500;
    color: #333;
    transform: translateY(-2px);
}
```

---

## 📋 Card Styles

### Standard Card
```css
.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    border: 1px solid #f1f3f5;
    transition: all 0.3s;
}

.card:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}
```

### Stat Card (Dashboard)
```css
.stat-card {
    background: linear-gradient(135deg, #FFD700, #FFA500);
    color: #2c3e50;
    border-radius: 15px;
    border: none;
    padding: 20px;
    box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);
}

.stat-card h2 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2c3e50;
}

.stat-card .title {
    font-size: 0.8rem;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.7);
    text-transform: uppercase;
}
```

### Service Card
```css
.service-card {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.3s;
}

.service-card:hover {
    border-color: #FFBF00;
    background: #fffbf0;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 191, 0, 0.3);
}
```

---

## 🏷️ Badge Styles

### Status Badges
```css
.status-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* REQUEST Status */
.status-request {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    color: #856404;
}

/* BOOKED Status */
.status-booked {
    background: linear-gradient(135deg, #cce5ff 0%, #b8daff 100%);
    color: #004085;
}

/* IN PROGRESS Status */
.status-in-progress {
    background: linear-gradient(135deg, #e7e5ff 0%, #d4d0ff 100%);
    color: #5a32a3;
}

/* CONFIRMED Status */
.status-confirmed {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    color: #155724;
}
```

---

## 📊 Table Styles

### Modern Table
```css
.table-modern {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.table-modern thead {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.table-modern th {
    padding: 15px;
    font-weight: 600;
    color: #495057;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #dee2e6;
}

.table-modern tbody tr {
    border-bottom: 1px solid #f1f3f5;
    transition: all 0.3s;
}

.table-modern tbody tr:hover {
    background: rgba(102, 126, 234, 0.03);
}

.table-modern td {
    padding: 15px;
    color: #495057;
    font-size: 0.95rem;
}
```

---

## 📝 Form Styles

### Input Fields
```css
.form-control {
    padding: 10px 15px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 0.95rem;
    transition: all 0.3s;
    background: white;
}

.form-control:focus {
    outline: none;
    border-color: #FFBF00;
    box-shadow: 0 0 0 3px rgba(255, 191, 0, 0.1);
}
```

### Labels
```css
.form-label {
    color: #495057;
    font-weight: 600;
    margin-bottom: 8px;
    font-size: 0.9rem;
}
```

---

## 🎭 Modal Styles

### Modal Header
```css
.modal-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 12px 12px 0 0;
}

.modal-header .modal-title {
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
}
```

### Modal Body
```css
.modal-body {
    padding: 20px;
    background: white;
}
```

---

## 🖼️ Layout Components

### Page Container
```css
.page-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
```

### Header Section
```css
.page-header {
    background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%);
    border-radius: 12px;
    padding: 20px 25px;
    margin-bottom: 25px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #495057;
    display: flex;
    align-items: center;
    gap: 12px;
}
```

### Day Card (Run-Down Plan)
```css
.day-card {
    background: white;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    overflow: hidden;
}

.day-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
```

---

## ⚡ Animation & Transitions

### Hover Animations
```css
/* Standard Hover */
transition: all 0.3s ease;

/* On Hover - Lift Effect */
transform: translateY(-2px);
box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);

/* Smooth Bounce */
transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Pulse Animation (Status)
```css
@keyframes statusPulse {
    0%, 100% {
        box-shadow: 0 10px 30px rgba(255, 140, 0, 0.4),
                    0 0 0 10px rgba(255, 140, 0, 0.1);
    }
    50% {
        box-shadow: 0 10px 30px rgba(255, 140, 0, 0.6),
                    0 0 0 15px rgba(255, 140, 0, 0.15);
    }
}

animation: statusPulse 2.5s infinite;
```

---

## 🎨 Typography

### Font Families
```css
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

/* For Print/Vouchers */
font-family: Georgia, serif;
```

### Font Weights
```css
font-weight: 400;  /* Regular */
font-weight: 600;  /* Semi-bold - Most common */
font-weight: 700;  /* Bold - Headers */
```

### Font Sizes
```css
/* Headers */
h1: 1.75rem - 2.5rem
h2: 1.5rem
h3: 1.25rem

/* Body */
body: 0.95rem
small: 0.85rem
tiny: 0.75rem
```

---

## 🎯 Icon Colors

```css
/* Primary Icons */
color: #667eea;  /* Purple-blue for service icons */

/* Accent Icons */
color: #FFBF00;  /* Yellow/gold for highlights */

/* Dark Icons */
color: #223A5E;  /* Navy blue for primary icons */
```

---

## 📐 Border Radius Guidelines

```css
/* Buttons & Small Elements */
border-radius: 8px;

/* Cards */
border-radius: 12px;

/* Large Cards/Containers */
border-radius: 15px;

/* Badges/Pills */
border-radius: 20px;

/* Circles */
border-radius: 50%;
```

---

## 🔧 Box Shadow Guidelines

```css
/* Light Shadow - Cards */
box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);

/* Medium Shadow - Hover State */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);

/* Accent Shadow - Yellow Elements */
box-shadow: 0 4px 15px rgba(255, 165, 0, 0.3);

/* Purple Shadow */
box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
```

---

## 🌟 Usage Guidelines

### When to Use Yellow/Gold (#FFBF00)
- Primary action buttons
- Important status indicators
- Call-to-action elements
- Hover states
- Active/selected states
- Stat cards on dashboard

### When to Use Purple (#667eea)
- Secondary actions
- Date headers
- Alternative accent color
- Dashboard sections
- Modal headers

### When to Use Navy Blue (#223A5E)
- Navigation
- Headers
- Main text
- Sidebar
- Professional elements

### When to Use Gradients
- Buttons for visual depth
- Stat cards for modern look
- Status indicators for hierarchy
- Headers for visual interest
- Hover states for feedback

---

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile */
@media (max-width: 768px) {
    /* Stack elements vertically */
    /* Increase touch targets */
    /* Simplify layouts */
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
    /* Optimize for medium screens */
}

/* Desktop */
@media (min-width: 1025px) {
    /* Full featured layout */
}
```

---

## ✅ Design Principles

1. **Consistency**: Use the same yellow/gold (#FFBF00) throughout for primary actions
2. **Hierarchy**: Yellow for primary, purple for secondary, navy for structure
3. **Contrast**: Always ensure text is readable against backgrounds
4. **Spacing**: Generous padding and margins (15px-25px typical)
5. **Feedback**: Hover states on all interactive elements
6. **Modern**: Use gradients, shadows, and smooth transitions
7. **Professional**: Clean, minimal design with purpose
8. **Accessible**: Maintain color contrast ratios for readability
