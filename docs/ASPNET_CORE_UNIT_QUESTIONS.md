# ASP.NET Core MVC – Unit-Wise Question Bank

**Course:** ASP.Net Core (BCA1604)  
**Programme:** BCA-III (CBCS) | Semester VI | Paper XII  
**Paper Type:** DSC 2G | Credits: 04 | UA: 80 | CA: 20

---

## 📋 Table of Contents

1. [Unit 1 – Introduction to ASP.Net Core MVC](#unit-1)
2. [Unit 2 – Entity Framework Core](#unit-2)
3. [Unit 3 – Model, View, Controller and Routing](#unit-3)
4. [Unit 4 – HTML, Tag Helper, Data Annotation Validation and State Management](#unit-4)
5. [Previous Year Exam Questions (March/April 2025)](#previous-year)

---

<a name="unit-1"></a>
## Unit 1: Introduction to ASP.Net Core MVC *(10 Marks)*

**Syllabus Topics:** Overview of Microsoft Web Technologies, ASP.NET Core Framework, .NET Core Environment Setup, Project File Structure, Main Method, InProcess/OutOfProcess Hosting, LaunchSettings.json, AppSettings.json, Middleware Components, Web Root (wwwroot), Static Files Middleware, Default Page, Developer Exception Page, CLI, Project Templates, MVC Framework Setup, Models, Controllers, Views, Dependency Injection.

---

### 1.1 Multiple Choice Questions (MCQs)

**1.** Which of the following is **not** a feature of ASP.NET Core?  
- a) Separation of Concerns  
- b) Testability  
- c) Built-in Authentication  
- **d) View State** ✅ *(View State belongs to classic ASP.NET WebForms, not ASP.NET Core)*

**2.** Which folder in ASP.NET Core serves static files (CSS, JS, images) to clients?  
- a) `/App_Data`  
- b) `/Content`  
- **c) `/wwwroot`** ✅  
- d) `/Resources`

**3.** What is the purpose of the `LaunchSettings.json` file?  
- a) To configure the database connection  
- **b) To configure the environment settings for launching the application during development** ✅  
- c) To define middleware pipeline  
- d) To set up NuGet packages

**4.** The `appsettings.json` file is used for:  
- a) Storing HTML templates  
- **b) Storing application configuration settings like connection strings, logging levels** ✅  
- c) Defining routing rules  
- d) Registering services for dependency injection

**5.** InProcess hosting in ASP.NET Core means:  
- **a) The application runs inside the IIS worker process (w3wp.exe)** ✅  
- b) The application runs in a separate process managed by Kestrel  
- c) The application uses an external web server  
- d) The application is hosted in Docker

**6.** Which middleware in ASP.NET Core is used to serve static files from the `wwwroot` folder?  
- a) `UseRouting()`  
- **b) `UseStaticFiles()`** ✅  
- c) `UseDefaultFiles()`  
- d) `UseAuthorization()`

**7.** What does the `Main()` method in an ASP.NET Core application do?  
- a) Handles HTTP requests  
- **b) Serves as the entry point that builds and runs the host** ✅  
- c) Registers controllers  
- d) Configures the database

**8.** The `Developer Exception Page` middleware should be enabled in which environment?  
- **a) Development** ✅  
- b) Production  
- c) Staging  
- d) Testing

**9.** Which component in MVC handles the incoming HTTP request, works with the model, and selects a view to render?  
- a) Model  
- b) View  
- **c) Controller** ✅  
- d) Middleware

**10.** Which of the following is a powerful feature of ASP.NET Core that helps manage object dependencies within an application?  
- a) Routing  
- b) Middleware  
- **c) Dependency Injection** ✅  
- d) View Engine

---

### 1.2 Fill in the Blanks

1. _______ is the built-in middleware in ASP.NET Core that handles serving static files. *(UseStaticFiles)*
2. The _______ folder in ASP.NET Core is the web root and serves static content. *(wwwroot)*
3. _______ is a powerful feature that helps manage object dependencies within our application. *(Dependency Injection)*
4. The _______ method is the entry point of an ASP.NET Core web application. *(Main)*
5. _______ in the MVC Design Pattern handle the incoming HTTP Request, work with the model, and select a view to render. *(Controllers)*
6. The _______ hosting model runs the ASP.NET Core app in a separate process from the IIS worker process. *(OutOfProcess)*

---

### 1.3 Short Answer Questions (2 Marks Each)

**a) Define Web Root Folder.**  
The **Web Root Folder** (`wwwroot`) is the folder in an ASP.NET Core application that contains all static files such as CSS, JavaScript, images, and HTML files that are directly accessible by clients (browsers) over HTTP. It acts as the document root for the application. Only the content inside `wwwroot` is served to clients; other application files are not directly accessible. The `UseStaticFiles()` middleware enables serving files from this folder.

**b) Explain InProcess Hosting and OutOfProcess Hosting.**  
- **InProcess Hosting:** The ASP.NET Core application runs inside the IIS worker process (`w3wp.exe`). Only one web server (IIS) handles requests, making it faster because there is no overhead of forwarding requests between processes.  
- **OutOfProcess Hosting:** The ASP.NET Core application runs in a separate process (using Kestrel web server), and IIS acts as a reverse proxy, forwarding requests to the Kestrel process. There is slight overhead due to inter-process communication but provides more isolation.

**c) What is Middleware in ASP.NET Core?**  
Middleware are components assembled into the application pipeline to handle HTTP requests and responses. Each middleware component can perform operations before and after calling the next component in the pipeline. Middleware is configured in the `Configure` method using methods like `UseRouting()`, `UseStaticFiles()`, `UseAuthentication()`, etc. Examples include Static Files Middleware, Authentication Middleware, and Developer Exception Page Middleware.

**d) What is the purpose of `appsettings.json`?**  
`appsettings.json` is a JSON configuration file in ASP.NET Core that stores application-level settings such as database connection strings, logging configuration, API keys, and custom application settings. It replaces the `Web.config` file used in older ASP.NET. Environment-specific overrides can be placed in `appsettings.Development.json` or `appsettings.Production.json`.

---

### 1.4 Long Answer Questions (10 Marks)

**Q. Explain the creation of an ASP.NET Core MVC Web Application covering project file structure, Main method, hosting options, and configuration files.**

#### Answer:

**1. Creating an ASP.NET Core MVC Application:**
- Install Visual Studio 2022, .NET 8 SDK
- File → New → Project → ASP.NET Core Web App (MVC) → Target .NET 8
- Visual Studio creates the project with default structure

**2. Project File Structure:**
```
MyApp/
├── Controllers/         - Controller classes (handle requests)
├── Models/              - Data model classes
├── Views/               - Razor view files (.cshtml)
│   ├── Home/
│   ├── Shared/
│   └── _ViewImports.cshtml
├── wwwroot/             - Static files (CSS, JS, images)
├── Properties/
│   └── launchSettings.json
├── appsettings.json     - Configuration settings
├── appsettings.Development.json
├── Program.cs           - Entry point (Main method)
└── MyApp.csproj         - Project file
```

**3. Main Method / Program.cs (NET 8):**
```csharp
var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();

var app = builder.Build();

// Configure the HTTP request pipeline (Middleware).
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
```

**4. Hosting Options:**
- **InProcess:** App runs inside IIS worker process. Set `<AspNetCoreHostingModel>InProcess</AspNetCoreHostingModel>` in `.csproj`.
- **OutOfProcess:** App runs in Kestrel; IIS forwards requests.

**5. Configuration Files:**
- `launchSettings.json`: Development environment launch settings (port, environment variables)
- `appsettings.json`: Production configuration
- `appsettings.Development.json`: Development overrides

**6. MVC Setup:**
- Controllers go in `Controllers/` and inherit from `Controller`
- Views use Razor syntax (`.cshtml`) in `Views/`
- Models are plain C# classes in `Models/`
- Dependency Injection is registered in `Program.cs` using `builder.Services`

---

<a name="unit-2"></a>
## Unit 2: Entity Framework Core *(15 Marks)*

**Syllabus Topics:** Introduction to EF Core, Installation, DbContext, Database Connection String, CRUD Operations, Entity States, Data Annotation Attributes (Table, Column, Key, ForeignKey, Index, InverseProperty, NotMapped, Required, MaxLength, MinLength, DatabaseGenerated, TimeStamp, ConcurrencyCheck), Relationships (One-to-One, One-to-Many, Many-to-Many, Self-Referencing), Async Programming, Disconnected Entities, Stored Procedures, Transactions, Migration, Database Seeding, Database First Approach.

---

### 2.1 Multiple Choice Questions (MCQs)

**1.** What is Entity Framework Core in ASP.NET?  
- a) A database management tool  
- b) A client-side scripting framework  
- **c) An ORM (Object-Relational Mapper)** ✅  
- d) A server-side state management tool

**2.** After creating a migration, the command used to sync the code base with the database is:  
- a) `Add-Migration`  
- **b) `Update-Database`** ✅  
- c) `Scaffold-DbContext`  
- d) `Enable-Migrations`

**3.** Which attribute marks a property as the primary key in Entity Framework Core?  
- a) `[PrimaryKey]`  
- **b) `[Key]`** ✅  
- c) `[Identity]`  
- d) `[Index]`

**4.** The `DbContext` class in EF Core is responsible for:  
- a) Handling HTTP requests  
- **b) Managing database connections and performing database operations** ✅  
- c) Rendering views  
- d) Validating model data

**5.** Which of the following represents a One-to-Many relationship in EF Core?  
- a) A student has one address  
- **b) A department has many employees** ✅  
- c) A student enrolls in many courses and a course has many students  
- d) An employee reports to themselves

**6.** The `[NotMapped]` attribute in EF Core tells the framework to:  
- **a) Exclude the property from the database table** ✅  
- b) Map the property to a computed column  
- c) Mark the property as a primary key  
- d) Set the property as required

**7.** Which NuGet package is used to install EF Core with SQL Server?  
- a) `Microsoft.EntityFrameworkCore`  
- **b) `Microsoft.EntityFrameworkCore.SqlServer`** ✅  
- c) `System.Data.SqlClient`  
- d) `EntityFramework6`

**8.** The `[Required]` attribute in EF Core Data Annotations:  
- a) Sets a maximum string length  
- **b) Makes the field non-nullable / required** ✅  
- c) Generates a default value  
- d) Maps to a specific column name

**9.** What does the `[ForeignKey]` attribute specify in EF Core?  
- a) The primary key of the entity  
- **b) The foreign key property in a relationship** ✅  
- c) The index on a column  
- d) The table name

**10.** Database Seeding in EF Core refers to:  
- a) Dropping all database tables  
- **b) Populating the database with initial/default data** ✅  
- c) Backing up the database  
- d) Migrating the database schema

---

### 2.2 Fill in the Blanks

1. EF Core is an _______ (Object-Relational Mapper) that lets you work with a database using .NET objects. *(ORM)*
2. The _______ command is used to create a new migration in EF Core Package Manager Console. *(Add-Migration)*
3. After creating a migration, we sync with the database using _______ command. *(Update-Database)*
4. The _______ class represents a session with the database and is used for querying and saving data. *(DbContext)*
5. The _______ attribute is used to define that a property is a primary key in EF Core. *([Key])*
6. _______ in EF Core refers to populating the database with initial or seed data. *(Database Seeding)*

---

### 2.3 Short Answer Questions (2 Marks Each)

**a) Define Key Attribute.**  
The `[Key]` attribute in Entity Framework Core is a **Data Annotation** used to specify that a property is the **primary key** of the entity/table. By convention, EF Core treats a property named `Id` or `<EntityName>Id` as the primary key. The `[Key]` attribute is used when the property has a different name.  
Example:
```csharp
public class Employee
{
    [Key]
    public int EmpNo { get; set; }
    public string Name { get; set; }
}
```

**b) Define Database Connection String in Entity Framework Core.**  
A **Database Connection String** specifies the information needed to connect to a database server, including server name, database name, authentication credentials, and other settings. In EF Core, it is typically stored in `appsettings.json` under the `ConnectionStrings` section and referenced in `DbContext` configuration.  
Example in `appsettings.json`:
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=EmpDB;Trusted_Connection=True;"
  }
}
```
Usage in `Program.cs`:
```csharp
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));
```

**c) Define Transactions in Entity Framework Core.**  
A **Transaction** in EF Core is a unit of work in which multiple database operations are executed together. Either all operations succeed (commit) or none of them are applied (rollback), ensuring data integrity. EF Core wraps `SaveChanges()` in a transaction by default. For explicit transactions:
```csharp
using var transaction = await context.Database.BeginTransactionAsync();
try {
    // perform operations
    await context.SaveChangesAsync();
    await transaction.CommitAsync();
} catch {
    await transaction.RollbackAsync();
}
```

**d) Define One-to-One Relationships.**  
A **One-to-One relationship** in EF Core means each record in one table corresponds to exactly one record in another table. For example, each Employee has one EmployeeProfile.  
```csharp
public class Employee {
    public int Id { get; set; }
    public EmployeeProfile Profile { get; set; }
}
public class EmployeeProfile {
    public int Id { get; set; }
    public int EmployeeId { get; set; }
    [ForeignKey("EmployeeId")]
    public Employee Employee { get; set; }
}
```

---

### 2.4 Long Answer Questions (10 Marks)

**Q. Write a note on DbContext in Entity Framework Core in detail.**

#### Answer:

**DbContext** is the primary class in Entity Framework Core that acts as a **bridge between your C# domain classes and the database**. It manages database connections, tracks changes to entities, and performs CRUD operations.

**Key Responsibilities of DbContext:**
1. **Database Connection Management** – Opens/closes connections automatically
2. **Querying** – Uses LINQ queries to fetch data
3. **Change Tracking** – Tracks modifications to entities (Added, Modified, Deleted, Unchanged)
4. **Saving Changes** – Persists tracked changes to the database via `SaveChanges()`
5. **Relationship Management** – Manages navigation properties and foreign keys

**Creating a DbContext:**
```csharp
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    // DbSet represents each table in the database
    public DbSet<Employee> Employees { get; set; }
    public DbSet<Department> Departments { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Fluent API configurations
        modelBuilder.Entity<Employee>()
            .HasOne(e => e.Department)
            .WithMany(d => d.Employees)
            .HasForeignKey(e => e.DepartmentId);
    }
}
```

**Registering DbContext in Program.cs:**
```csharp
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));
```

**Entity States in DbContext:**

| State | Description |
|-------|-------------|
| Added | Entity is new; will be INSERTed |
| Modified | Entity has been changed; will be UPDATEd |
| Deleted | Entity marked for deletion; will be DELETEd |
| Unchanged | No changes; no action taken |
| Detached | Not tracked by DbContext |

**CRUD with DbContext:**
```csharp
// Create
context.Employees.Add(new Employee { Name = "Raj" });
context.SaveChanges();

// Read
var emp = context.Employees.Find(1);

// Update
emp.Name = "Rahul";
context.SaveChanges();

// Delete
context.Employees.Remove(emp);
context.SaveChanges();
```

**Best Practices:**
- Register DbContext with `Scoped` lifetime (one instance per request)
- Use `async`/`await` methods (`SaveChangesAsync`, `ToListAsync`)
- Dispose properly (handled automatically via DI)

---

**Q. Explain CRUD Operations in Entity Framework Core in Detail with Example.**

#### Answer:

**CRUD** = **C**reate, **R**ead, **U**pdate, **D**elete — the four basic database operations.

**Model:**
```csharp
public class Student {
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}
```

**1. CREATE (Insert):**
```csharp
public async Task CreateStudent(Student student) {
    _context.Students.Add(student);
    await _context.SaveChangesAsync();
}
```

**2. READ (Select):**
```csharp
// Get all students
var all = await _context.Students.ToListAsync();

// Get by ID
var student = await _context.Students.FindAsync(id);

// With filtering
var filtered = await _context.Students
    .Where(s => s.Name.Contains("Raj"))
    .ToListAsync();
```

**3. UPDATE:**
```csharp
public async Task UpdateStudent(Student student) {
    _context.Entry(student).State = EntityState.Modified;
    await _context.SaveChangesAsync();
}
```

**4. DELETE:**
```csharp
public async Task DeleteStudent(int id) {
    var student = await _context.Students.FindAsync(id);
    if (student != null) {
        _context.Students.Remove(student);
        await _context.SaveChangesAsync();
    }
}
```

**Migration Commands:**
```bash
Add-Migration InitialCreate    # Create migration
Update-Database                # Apply to database
Remove-Migration               # Undo last migration
```

---

**Q. Define Data Annotation Attributes in Entity Framework Core.**

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `[Table("tbl_Name")]` | Map to specific table name | `[Table("Students")]` |
| `[Column("col_Name")]` | Map to specific column name | `[Column("Emp_Name")]` |
| `[Key]` | Primary key | `[Key] public int Id` |
| `[ForeignKey("PropName")]` | Foreign key | `[ForeignKey("DeptId")]` |
| `[Required]` | NOT NULL constraint | `[Required] public string Name` |
| `[MaxLength(100)]` | Maximum string length | `[MaxLength(50)]` |
| `[MinLength(2)]` | Minimum string length | `[MinLength(2)]` |
| `[NotMapped]` | Exclude from DB | `[NotMapped] public string FullName` |
| `[Index]` | Create database index | `[Index(IsUnique = true)]` |
| `[DatabaseGenerated]` | Auto-generated values | `[DatabaseGenerated(DatabaseGeneratedOption.Identity)]` |
| `[Timestamp]` | Row version for concurrency | `[Timestamp] public byte[] RowVersion` |
| `[ConcurrencyCheck]` | Optimistic concurrency | `[ConcurrencyCheck] public string Name` |

---

<a name="unit-3"></a>
## Unit 3: Model, View, Controller and Routing *(20 Marks)*

**Syllabus Topics:** ViewData, ViewBag, Strongly Typed View, ViewModel, TempData, PRG Pattern, Layout View, Sections, ViewStart, ViewImports, Partial Views, View Components, Razor Syntax, Bootstrap, Action Results, Routing, Custom Route Constraints, Attribute Routing, Attribute vs Conventional Routing, Model Binding (FromForm, FromQuery, FromRoute, FromHeader, FromBody, Complex Type, Custom).

---

### 3.1 Multiple Choice Questions (MCQs)

**1.** What is the purpose of routing in ASP.NET Core MVC?  
- **a) To map URLs to controller actions** ✅  
- b) To manage session state  
- c) To authenticate users  
- d) To validate user input

**2.** What is the use of the `ViewBag` object?  
- **a) To pass data from the controller to the view** ✅  
- b) To pass data from the view to the controller  
- c) To store session data  
- d) To cache frequently accessed data

**3.** Which of the following is **not** a valid action result type in ASP.NET Core MVC?  
- a) ViewResult  
- b) JsonResult  
- c) FileResult  
- **d) QueryResult** ✅ *(Not a valid type)*

**4.** What does the **View** in MVC represent?  
- **a) User Interface** ✅  
- b) Application Logic  
- c) Database Structure  
- d) Ensure security

**5.** Which of the following is **not** a valid way to pass data from a controller to a view in ASP.NET Core MVC?  
- a) ViewBag  
- b) ViewData  
- c) TempData  
- **d) HttpRequest** ✅

**6.** Which component in MVC handles the business logic?  
- **a) Model** ✅  
- b) View  
- c) Controller  
- d) Handler

**7.** _______ is a dictionary object that allows you to pass data from the controller to the view using key-value pairs.  
- a) ViewBag  
- **b) ViewData** ✅  
- c) TempData  
- d) Session

**8.** Which action result type formats data as JSON and sends it as a response?  
- a) ViewResult  
- **b) JsonResult** ✅  
- c) ContentResult  
- d) FileResult

**9.** Attribute routing in ASP.NET Core is configured using:  
- **a) `[Route]` attribute on controller/action** ✅  
- b) `MapControllerRoute()` in `Program.cs`  
- c) Middleware  
- d) `appsettings.json`

**10.** Which Model Binding source is used to bind data from the URL query string?  
- a) `[FromBody]`  
- b) `[FromRoute]`  
- **c) `[FromQuery]`** ✅  
- d) `[FromHeader]`

---

### 3.2 Fill in the Blanks

1. _______ is a dictionary object that allows you to pass data from the controller to the view using key-value pairs. *(ViewData)*
2. The _______ is a type of action result that formats the given data as JSON and sends it as a response. *(JsonResult)*
3. _______ in MVC stores data for the current request AND the next request (survives redirects). *(TempData)*
4. The _______ file in ASP.NET Core MVC automatically adds `@using` and `@addTagHelper` directives to all views. *(_ViewImports.cshtml)*
5. _______ routing allows you to define routes directly on controller actions using attributes. *(Attribute)*
6. The _______ pattern is used to prevent duplicate form submissions by redirecting after a POST. *(Post-Redirect-Get / PRG)*

---

### 3.3 Short Answer Questions (2 Marks Each)

**a) Define View Result.**  
A **ViewResult** is an action result in ASP.NET Core MVC that renders a **Razor view** (`.cshtml` file) as an HTML response. When a controller action returns `View()`, it returns a `ViewResult` that looks for a corresponding `.cshtml` file in the `Views/<ControllerName>/` folder.  
```csharp
public IActionResult Index() {
    return View(); // Returns ViewResult
}
```

**b) Define FromQuery Model Binding.**  
`[FromQuery]` is a **Model Binding** attribute that tells ASP.NET Core MVC to bind a parameter's value from the **URL query string** (the part after `?` in a URL).  
```csharp
// URL: /products?name=Phone&price=500
public IActionResult Search([FromQuery] string name, [FromQuery] int price) {
    // name = "Phone", price = 500
}
```

**c) Define Layout View.**  
A **Layout View** in ASP.NET Core MVC is a master page (template) that defines the common structure/layout (header, footer, navigation) shared across multiple views. Individual views render inside the layout's `@RenderBody()` placeholder. It is typically stored as `_Layout.cshtml` in `Views/Shared/`. Layouts reduce code duplication across pages.

**d) Define Views.**  
A **View** in ASP.NET Core MVC is the component responsible for rendering the **user interface (UI)**. Views are Razor files (`.cshtml`) that contain a mix of HTML and C# code. They display data passed by the controller and handle how information is presented to the user. Views are stored in the `Views/` folder, typically organized by controller name.

---

### 3.4 Long Answer Questions

**Q. Define TempData in ASP.NET Core MVC.**

**TempData** is a mechanism to pass data between **two consecutive requests** (typically from a POST action to a GET action after a redirect). Unlike `ViewData` and `ViewBag` which only live for the current request, `TempData` persists data until it is read in the next request.

**Key Characteristics:**
- Stores data in a dictionary (`TempData["key"] = value`)
- Data is available in the next request and deleted after it is read
- Useful in **Post-Redirect-Get (PRG)** pattern
- Uses session or cookies to store data between requests

**Usage Example:**
```csharp
// In POST action:
[HttpPost]
public IActionResult Create(Employee emp) {
    _context.Employees.Add(emp);
    _context.SaveChanges();
    TempData["SuccessMessage"] = "Employee added successfully!";
    return RedirectToAction("Index");
}

// In GET action:
public IActionResult Index() {
    // TempData["SuccessMessage"] is available here
    return View();
}
```

**In View:**
```html
@if (TempData["SuccessMessage"] != null) {
    <div class="alert alert-success">@TempData["SuccessMessage"]</div>
}
```

**TempData.Keep() and TempData.Peek():**
- `TempData.Keep("key")` – Keeps the value for another request
- `TempData.Peek("key")` – Reads value without marking it for deletion

---

**Q. Define ViewData, ViewBag, Strongly Typed View, and ViewModel in Detail.**

#### 1. ViewData
- **Type:** `ViewDataDictionary` (key-value dictionary)
- **Scope:** Current request only
- **Type Safety:** Requires casting when reading
- **Usage:** Pass simple data from Controller to View

```csharp
// Controller
ViewData["Title"] = "Home Page";
ViewData["Count"] = 42;

// View
<h1>@ViewData["Title"]</h1>
<p>Count: @(int)ViewData["Count"]</p>
```

#### 2. ViewBag
- **Type:** Dynamic object (wraps ViewData)
- **Scope:** Current request only
- **Type Safety:** No casting needed (uses `dynamic`)
- **Usage:** Convenient shorthand for ViewData

```csharp
// Controller
ViewBag.Title = "Home Page";
ViewBag.Employees = employeeList;

// View
<h1>@ViewBag.Title</h1>
```

**Note:** `ViewBag` and `ViewData` share the same underlying dictionary. Setting `ViewData["Key"]` is same as `ViewBag.Key`.

#### 3. Strongly Typed View
A view that is bound to a specific model type using `@model` directive. It provides **IntelliSense, compile-time type checking**, and is the recommended approach.

```csharp
// Controller
public IActionResult Details(int id) {
    var emp = _context.Employees.Find(id);
    return View(emp); // Passes Employee model
}
```
```html
<!-- View with @model directive -->
@model Employee
<h1>@Model.Name</h1>
<p>@Model.Email</p>
```

#### 4. ViewModel
A **ViewModel** is a custom C# class designed specifically to hold data for a particular view. It can combine data from multiple models/entities that a view needs.

```csharp
// ViewModel
public class EmployeeDashboardViewModel {
    public Employee Employee { get; set; }
    public List<Attendance> AttendanceHistory { get; set; }
    public int LeaveBalance { get; set; }
}

// Controller
public IActionResult Dashboard(int id) {
    var vm = new EmployeeDashboardViewModel {
        Employee = _context.Employees.Find(id),
        AttendanceHistory = _context.Attendance.Where(a => a.EmpId == id).ToList(),
        LeaveBalance = 12
    };
    return View(vm);
}
```

**Comparison Table:**

| Feature | ViewData | ViewBag | Strongly Typed View | ViewModel |
|---------|---------|---------|---------------------|-----------|
| Type Safety | No (casting needed) | No (dynamic) | Yes | Yes |
| IntelliSense | No | No | Yes | Yes |
| Scope | Request | Request | Request | Request |
| Best For | Simple data | Simple data | Single model | Multiple models |
| Null Error Risk | Runtime | Runtime | Compile-time | Compile-time |

---

<a name="unit-4"></a>
## Unit 4: HTML, Tag Helper, Data Annotation Validation and State Management *(15 Marks)*

**Syllabus Topics:** HTML Helpers (TextBox, TextArea, DropDownList, RadioButton, CheckBox, ListBox, Password, Hidden, Custom), Form Using HTML Helpers, Links in MVC, Tag Helpers (Image, Environment, Navigation, Form, Partial, Custom, View Component, Cache), Data Annotations, Model Validations, Custom Annotation, Remote Validation, Blacklist/Whitelist Checks, Cookies (Encrypt, Persistent vs Non-Persistent), Sessions (In-Memory vs Distributed), Upload/Delete Files, Export to Excel, Import Excel, Generate PDF, Send Email.

---

### 4.1 Multiple Choice Questions (MCQs)

**1.** The `@Html` helper is used _______.  
- **a) To create HTML elements** ✅  
- b) To validate user input  
- c) To serialize data  
- d) To manage session state

**2.** How can you specify a required field in a model using data annotations in ASP.NET Core MVC?  
- **a) `[Required]`** ✅  
- b) `[Mandatory]`  
- c) `[NotNull]`  
- d) `[DataRequired]`

**3.** Which of the following is used to create a dropdown list using HTML Helpers?  
- a) `@Html.TextBox()`  
- **b) `@Html.DropDownList()`** ✅  
- c) `@Html.RadioButton()`  
- d) `@Html.ListBox()`

**4.** The difference between Persistent and Non-Persistent cookies is:  
- a) Persistent cookies are encrypted; non-persistent are not  
- **b) Persistent cookies have an expiry date and survive browser close; non-persistent are deleted when browser closes** ✅  
- c) Persistent cookies are stored on server; non-persistent on client  
- d) There is no difference

**5.** Which attribute is used for remote validation in ASP.NET Core MVC?  
- a) `[Remote]` with GET method  
- **b) `[Remote]` attribute** ✅  
- c) `[Validate]`  
- d) `[AjaxValidate]`

**6.** Sessions in ASP.NET Core are stored:  
- a) On the client-side in cookies  
- **b) On the server-side (in memory or distributed cache)** ✅  
- c) In the database automatically  
- d) In local storage

**7.** Which Tag Helper is used to create a form in ASP.NET Core MVC?  
- a) `<form>` with `method` attribute  
- **b) `<form asp-action="Action" asp-controller="Controller">` tag helper** ✅  
- c) `@Html.BeginForm()`  
- d) `<asp:form>`

**8.** In ASP.NET Core MVC, the `[MaxLength(50)]` data annotation:  
- a) Validates that the value is exactly 50 characters  
- **b) Validates that the string is not longer than 50 characters** ✅  
- c) Sets a default value of 50  
- d) Creates a database column of VARCHAR(50)

**9.** Which of the following is an example of a **whitelist** check using Data Annotations?  
- **a) Only allow email addresses ending in `@college.edu`** ✅  
- b) Block known spam email domains  
- c) Reject null values  
- d) Check string length

**10.** The `HttpOnly` flag on a cookie:  
- a) Makes the cookie visible only on HTTPS  
- **b) Prevents JavaScript from accessing the cookie, improving security** ✅  
- c) Makes the cookie expire after 1 hour  
- d) Encrypts the cookie value

---

### 4.2 Fill in the Blanks

1. _______ attribute is used to specify that a property is required in model validation. *([Required])*
2. _______ cookies have an expiry date and survive browser close, while session cookies are deleted when the browser closes. *(Persistent)*
3. The _______ attribute in ASP.NET Core MVC is used for server-side validation via an AJAX call to a controller action. *([Remote])*
4. HTML Helpers like `@Html.TextBoxFor()` are _______ typed helpers that use lambda expressions. *(Strongly)*
5. _______ are stored on the server side and identified by a session ID cookie sent to the browser. *(Sessions)*
6. The _______ validation attribute allows you to define a custom validation logic in a separate class by inheriting from `ValidationAttribute`. *(Custom Data Annotation)*

---

### 4.3 Short Answer Questions (2 Marks Each)

**a) Define Dropdown List (HTML Helper).**  
`@Html.DropDownList()` and `@Html.DropDownListFor()` are **HTML Helper methods** in ASP.NET Core MVC used to render an HTML `<select>` dropdown element. The `DropDownListFor()` is strongly typed and uses a lambda expression to bind to a model property.

```csharp
// Controller
ViewBag.Departments = new SelectList(departmentList, "Id", "Name");

// View
@Html.DropDownListFor(m => m.DepartmentId, 
    (SelectList)ViewBag.Departments, 
    "-- Select Department --", 
    new { @class = "form-control" })
```

**b) Explain Differences Between Cookies and Sessions.**

| Feature | Cookies | Sessions |
|---------|---------|---------|
| Storage | Client-side (browser) | Server-side |
| Security | Less secure (visible to client) | More secure |
| Capacity | ~4KB per cookie | Limited by server memory |
| Lifetime | Can be persistent or session-based | Ends when browser closes or timeout |
| Types | Persistent, Non-Persistent | In-Memory, Distributed |
| Access | Via `Request.Cookies` / `Response.Cookies` | Via `HttpContext.Session` |

**c) Blacklist and Whitelist Checks using Data Annotation.**  
- **Whitelist:** Only allows values from a predefined approved list (e.g., only allow `.edu` email domains)
- **Blacklist:** Rejects values that match a list of prohibited patterns (e.g., block known spam domains)

Both are implemented using **Custom Validation Attributes** by inheriting from `ValidationAttribute`.

```csharp
// Whitelist example: only allow approved email domains
public class WhitelistedEmailAttribute : ValidationAttribute {
    private readonly string[] _allowedDomains = { "gmail.com", "yahoo.com" };
    protected override ValidationResult IsValid(object value, ValidationContext ctx) {
        var email = value?.ToString();
        var domain = email?.Split('@').LastOrDefault();
        if (!_allowedDomains.Contains(domain))
            return new ValidationResult("Email domain not allowed.");
        return ValidationResult.Success;
    }
}
```

---

### 4.4 Long Answer Questions

**Q. Write a note on Model Validations in MVC.**

#### Answer:

**Model Validation** in ASP.NET Core MVC is the process of verifying that data submitted by the user meets defined rules before it is processed. ASP.NET Core provides built-in validation using **Data Annotations** and **Fluent Validation**.

**1. Built-in Validation Attributes:**

| Attribute | Description | Example |
|-----------|-------------|---------|
| `[Required]` | Field must have a value | `[Required(ErrorMessage = "Name is required")]` |
| `[MaxLength(n)]` | Maximum string length | `[MaxLength(100)]` |
| `[MinLength(n)]` | Minimum string length | `[MinLength(2)]` |
| `[Range(min, max)]` | Numeric range | `[Range(1, 100)]` |
| `[EmailAddress]` | Valid email format | `[EmailAddress]` |
| `[Phone]` | Valid phone format | `[Phone]` |
| `[Url]` | Valid URL format | `[Url]` |
| `[Compare]` | Compare two fields | `[Compare("Password")]` |
| `[RegularExpression]` | Regex pattern | `[RegularExpression(@"^\d{10}$")]` |
| `[StringLength]` | Min and max length | `[StringLength(50, MinimumLength = 2)]` |

**2. Model with Validation:**
```csharp
public class RegisterViewModel {
    [Required(ErrorMessage = "Name is required")]
    [StringLength(50, MinimumLength = 2)]
    public string Name { get; set; }

    [Required]
    [EmailAddress(ErrorMessage = "Invalid email")]
    public string Email { get; set; }

    [Required]
    [Range(18, 65, ErrorMessage = "Age must be between 18 and 65")]
    public int Age { get; set; }

    [Required]
    [DataType(DataType.Password)]
    public string Password { get; set; }

    [Compare("Password", ErrorMessage = "Passwords do not match")]
    public string ConfirmPassword { get; set; }
}
```

**3. Checking ModelState in Controller:**
```csharp
[HttpPost]
public IActionResult Register(RegisterViewModel model) {
    if (!ModelState.IsValid) {
        return View(model); // Return with validation errors
    }
    // Process valid model
    return RedirectToAction("Success");
}
```

**4. Displaying Validation in View:**
```html
@model RegisterViewModel
<form asp-action="Register">
    <div>
        <label asp-for="Name"></label>
        <input asp-for="Name" class="form-control" />
        <span asp-validation-for="Name" class="text-danger"></span>
    </div>
    <div>
        <label asp-for="Email"></label>
        <input asp-for="Email" class="form-control" />
        <span asp-validation-for="Email" class="text-danger"></span>
    </div>
    <button type="submit">Register</button>
    @Html.ValidationSummary(true, "", new { @class = "text-danger" })
</form>
@section Scripts {
    @await Html.PartialAsync("_ValidationScriptsPartial")
}
```

**5. Custom Validation Attribute:**
```csharp
public class FutureDateAttribute : ValidationAttribute {
    protected override ValidationResult IsValid(object value, ValidationContext ctx) {
        if (value is DateTime date && date <= DateTime.Today)
            return new ValidationResult("Date must be in the future.");
        return ValidationResult.Success;
    }
}
// Usage: [FutureDate] public DateTime JoiningDate { get; set; }
```

**6. Remote Validation:**
Remote validation uses AJAX to call a controller action for server-side validation without a full page reload.
```csharp
[AcceptVerbs("GET", "POST")]
public IActionResult IsEmailAvailable(string email) {
    bool exists = _context.Users.Any(u => u.Email == email);
    return exists ? Json("Email already in use.") : Json(true);
}
```
```csharp
[Remote(action: "IsEmailAvailable", controller: "User")]
public string Email { get; set; }
```

**7. Client-Side Validation:**  
ASP.NET Core MVC integrates with **jQuery Validation** and **jQuery Unobtrusive Validation** libraries. When the `_ValidationScriptsPartial` is included, validation runs in the browser without a server round-trip.

---

**Q. Explain any four HTML Helpers with controls in details.**

#### Answer:

HTML Helpers in ASP.NET Core MVC are C# methods that generate HTML elements. They come in two forms:
- **Standard:** `@Html.TextBox("name")`
- **Strongly Typed:** `@Html.TextBoxFor(m => m.PropertyName)`

---

**1. TextBox Helper**  
Renders an `<input type="text">` element.  
```csharp
// Standard
@Html.TextBox("Name", "", new { @class = "form-control", placeholder = "Enter name" })

// Strongly Typed (recommended)
@Html.TextBoxFor(m => m.Name, new { @class = "form-control" })
```
Output: `<input class="form-control" id="Name" name="Name" type="text" value="" />`

---

**2. TextArea Helper**  
Renders a `<textarea>` element for multi-line text input.  
```csharp
@Html.TextAreaFor(m => m.Description, 5, 50, new { @class = "form-control" })
// 5 = rows, 50 = columns
```
Output: `<textarea class="form-control" cols="50" id="Description" name="Description" rows="5"></textarea>`

---

**3. DropDownList Helper**  
Renders a `<select>` dropdown element.  
```csharp
// Controller
ViewBag.Cities = new SelectList(new[] { "Mumbai", "Pune", "Delhi" });

// View
@Html.DropDownListFor(m => m.City, 
    (SelectList)ViewBag.Cities, 
    "-- Select City --", 
    new { @class = "form-control" })
```
Output:  
```html
<select class="form-control" id="City" name="City">
    <option value="">-- Select City --</option>
    <option>Mumbai</option>
    <option>Pune</option>
    <option>Delhi</option>
</select>
```

---

**4. RadioButton Helper**  
Renders an `<input type="radio">` element.  
```csharp
@Html.RadioButtonFor(m => m.Gender, "Male") Male
@Html.RadioButtonFor(m => m.Gender, "Female") Female
```
Output:  
```html
<input id="Gender" name="Gender" type="radio" value="Male" /> Male
<input id="Gender" name="Gender" type="radio" value="Female" /> Female
```

---

**Additional Helpers (Quick Reference):**

| Helper | HTML Element | Usage |
|--------|-------------|-------|
| `@Html.CheckBoxFor()` | `<input type="checkbox">` | Boolean fields |
| `@Html.PasswordFor()` | `<input type="password">` | Password fields |
| `@Html.HiddenFor()` | `<input type="hidden">` | Hidden values |
| `@Html.LabelFor()` | `<label>` | Field labels |
| `@Html.ValidationMessageFor()` | `<span>` | Validation errors |
| `@Html.ListBox()` | `<select multiple>` | Multi-select lists |

---

<a name="previous-year"></a>
## Previous Year Exam Questions – March/April 2025

**Exam:** B.C.A. (Semester VI) (New) (CBCS)  
**Paper:** ASP.Net Core (BCA1604) | Date: Monday, 05-May-2025 | Max Marks: 80

---

### Q.1 A) Select the Correct Alternative *(10 Marks)*

1. Which of the following is not a feature of ASP.NET? → **d) View State**
2. Purpose of routing → **a) To map URLs to controller actions**
3. Use of ViewBag object → **a) To pass data from controller to view**
4. `@Html` helper is used → **a) To create HTML elements**
5. Not a valid action result type → **d) QueryResult**
6. What does View in MVC represent → **a) User Interface**
7. Not a valid way to pass data from controller to view → **d) HttpRequest**
8. Which component handles business logic → **a) Model**
9. Specify required field using data annotation → **a) [Required]**
10. What is Entity Framework in ASP.NET → **c) An ORM (Object-Relational Mapper)**

### Q.1 B) Fill in the Blanks *(6 Marks)*

1. _______ is a dictionary object to pass data using key-value pairs → **ViewData**
2. _______ formats data as JSON response → **JsonResult**
3. _______ middleware handles static files → **UseStaticFiles** (Static Files Middleware)
4. Sync code with database after migration → **Update-Database**
5. _______ handle incoming HTTP Request in MVC → **Controllers**
6. _______ manages object dependencies → **Dependency Injection**

---

### Q.2 Solve any Eight *(16 Marks – 2 Marks Each)*

| # | Topic | Unit |
|---|-------|------|
| a | Define Web root folder | Unit 1 |
| b | Explain Key Attribute | Unit 2 |
| c | Define FromQuery Model Binding | Unit 3 |
| d | Define View Result | Unit 3 |
| e | Define Transactions in EF Core | Unit 2 |
| f | Define Layout View | Unit 3 |
| g | Define One-to-One Relationships | Unit 2 |
| h | Define Database Connection String in EF Core | Unit 2 |
| i | Define Dropdown List | Unit 4 |
| j | Define Views | Unit 3 |

*(Refer to respective unit sections above for detailed answers)*

---

### Q.3 A) Attempt any Two *(10 Marks)*

1. Define Data Annotation Attributes in EF Core → *[See Unit 2 – Long Answer]*
2. Define TempData → *[See Unit 3 – Long Answer]*
3. Explain InProcess and OutOfProcess Hosting → *[See Unit 1 – Short Answer]*

**Q.3 B)** Write a note on DbContext in EF Core → *[See Unit 2 – Long Answer]*

---

### Q.4 Attempt any Two

**a)** Explain Differences between Cookies and Sessions → *[See Unit 4 – Short Answer]*  
**b)** Define Routing in ASP.NET Core MVC → *[See Unit 3 below]*  
**c)** Blacklist and Whitelist Checks using Data Annotation → *[See Unit 4 – Short Answer]*

**Q.4 B)** Write a note on Model Validations in MVC → *[See Unit 4 – Long Answer]*

#### Routing in ASP.NET Core MVC (Q4b)

**Routing** is the mechanism in ASP.NET Core MVC that **maps incoming HTTP requests (URLs) to specific controller actions**.

**Types of Routing:**

**1. Conventional Routing (defined in Program.cs):**
```csharp
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");
```
Example: `/Products/Details/5` → `ProductsController.Details(5)`

**2. Attribute Routing (defined on controllers/actions):**
```csharp
[Route("api/products")]
public class ProductsController : Controller
{
    [Route("{id:int}")]
    public IActionResult GetById(int id) { ... }

    [HttpGet("search")]
    public IActionResult Search([FromQuery] string name) { ... }
}
```

**3. Custom Route Constraints:**
```csharp
// Only match if id is an integer
[Route("products/{id:int}")]
// Only match specific values
[Route("status/{status:regex(^(active|inactive)$)}")]
```

**Conventional vs Attribute Routing:**

| Feature | Conventional | Attribute |
|---------|-------------|-----------|
| Defined In | `Program.cs` | Controller/Action |
| Flexibility | Less flexible | More flexible |
| REST APIs | Less suitable | Preferred |
| Visibility | Centralized | Scattered |

---

### Q.5 Attempt any Two

**a)** CRUD Operations in EF Core → *[See Unit 2 – Long Answer]*  
**b)** ViewData, ViewBag, Strongly Typed View, ViewModel → *[See Unit 3 – Long Answer]*  
**c)** Explain any four HTML Helpers → *[See Unit 4 – Long Answer]*

---

## 📊 Syllabus Coverage Summary

| Unit | Topics | Marks | Question Types |
|------|--------|-------|---------------|
| Unit 1 | MVC Intro, Hosting, Middleware, wwwroot | 10 | MCQ, Fill Blanks, 2-mark, 10-mark |
| Unit 2 | EF Core, DbContext, CRUD, Annotations | 15 | MCQ, Fill Blanks, 2-mark, 10-mark |
| Unit 3 | Views, Controllers, Routing, Model Binding | 20 | MCQ, Fill Blanks, 2-mark, 10-mark |
| Unit 4 | HTML Helpers, Validation, Cookies, Sessions | 15 | MCQ, Fill Blanks, 2-mark, 10-mark |

---

*Last Updated: March 2026 | Source: BCA-III (CBCS) Sem VI – ASP.NET Core (BCA1604)*
