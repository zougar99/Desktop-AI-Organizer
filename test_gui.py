"""Quick GUI test to confirm customtkinter window shows up."""
import customtkinter as ctk

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("Test Window")
app.geometry("500x300")

label = ctk.CTkLabel(app, text="If you see this, GUI works!", font=ctk.CTkFont(size=20, weight="bold"))
label.pack(expand=True)

btn = ctk.CTkButton(app, text="Click Me", command=lambda: label.configure(text="Button works!"))
btn.pack(pady=20)

print("Window created successfully, running mainloop...")
app.mainloop()
print("Window closed.")
