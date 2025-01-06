import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from PIL import Image,ImageTk

# Σύνδεση με τη βάση δεδομένων

# Λειτουργία για τον έλεγχο των στοιχείων σύνδεσης
def check_login():
    username = entry_username.get()
    password = entry_password.get()
    
    if username == "Admin" and password == "123456":
        # Αν οι πληροφορίες είναι σωστές, ανοίγουμε το επόμενο παράθυρο
        open_next_window()
    else:
        # Αν οι πληροφορίες είναι λάθος, εμφανίζουμε το μήνυμα σφάλματος
        messagebox.showerror("Σφάλμα Σύνδεσης", "Λάθος Όνομα Χρήστη ή Κωδικός")

def connect_to_db():
    try:
        conn = sqlite3.connect("AERODROMIO_FINAL.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()

        return conn, cursor
    except sqlite3.Error as e:
        messagebox.showerror("Σφάλμα Βάσης Δεδομένων", f"Πρόβλημα σύνδεσης: {e}")
        return None, None

# Λειτουργία για εμφάνιση δεδομένων πίνακα
def show_table_data(table_name, treeview, conn, cursor):
    # Καθαρισμός προηγούμενων δεδομένων
    for item in treeview.get_children():
        treeview.delete(item)

    try:
        # Εκτέλεση ερωτήματος για ανάκτηση δεδομένων
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Ορισμός στηλών
        treeview["columns"] = columns
        treeview["show"] = "headings"  # Απόκρυψη της πρώτης κενής στήλης

        # Δημιουργία επικεφαλίδων
        for col in columns:
            treeview.heading(col, text=col)
            treeview.column(col, width=120, anchor="center")

        # Εισαγωγή δεδομένων με το όνομα του πίνακα ως tags
        for row in rows:
            treeview.insert("", "end", values=row, tags=(table_name,))

    except sqlite3.Error as e:
        messagebox.showerror("Σφάλμα", f"Δεν είναι δυνατή η ανάκτηση δεδομένων: {e}")

def update_selected_row(selected_item, treeview, conn, cursor):
    if not selected_item:
        messagebox.showerror("Σφάλμα", "Δεν έχει επιλεγεί καμία γραμμή!")
        return

    table_name = treeview.item(selected_item)["tags"]
    if not table_name:
        messagebox.showerror("Σφάλμα", "Δεν είναι διαθέσιμο το όνομα του πίνακα!")
        return
    
    table_name = table_name[0]

    row_data = treeview.item(selected_item)["values"]

    # Ανίχνευση της στήλης του πρωτεύοντος κλειδιού
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    primary_key_column = None
    for col_info in columns_info:
        if col_info[5] == 1:  # Το πεδίο 'pk' είναι 1 για την στήλη του πρωτεύοντος κλειδιού
            primary_key_column = col_info[1]
            break

    if primary_key_column is None:
        messagebox.showerror("Σφάλμα", "Δεν βρέθηκε πρωτεύων κλειδί για τον πίνακα!")
        return

    update_window = tk.Toplevel()
    update_window.title("Ενημέρωση Στοιχείων")
    
    labels = []
    entries = []
    for i, (col, value) in enumerate(zip(treeview["columns"], row_data)):
        label = tk.Label(update_window, text=col)
        label.grid(row=i, column=0, padx=50, pady=5)
        entry = tk.Entry(update_window, font=("Arial", 12))
        entry.grid(row=i, column=1, padx=5, pady=5)
        entry.insert(0, value)
        labels.append(label)
        entries.append(entry)

    def on_ok():
        updated_values = [entry.get() for entry in entries]# if entry.get() != row_data[treeview["columns"].index(primary_key_column)]]
        new_primary_key_value = updated_values[treeview["columns"].index(primary_key_column)]
        row_id = row_data[treeview["columns"].index(primary_key_column)]
        update_data_in_db(updated_values, row_id, new_primary_key_value,primary_key_column, table_name, treeview, cursor, conn)
        update_window.destroy()

    def on_cancel():
        update_window.destroy()

    ok_button = tk.Button(update_window, text="OK", command=on_ok)
    ok_button.grid(row=len(row_data), column=0, padx=10, pady=5)

    cancel_button = tk.Button(update_window, text="Cancel", command=on_cancel)
    cancel_button.grid(row=len(row_data), column=1, padx=10, pady=5)

def update_data_in_db(updated_values, row_id, new_primary_key_value, primary_key_column, table_name, treeview, cursor, conn):
    try:
        columns = [column for column in treeview["columns"]] #if column != primary_key_column]
        set_clause = ", ".join([f"{column} = ?" for column in columns])
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key_column} = ?"
        cursor.execute(update_query, updated_values + [row_id])

        # Αν το πρωτεύον κλειδί έχει αλλάξει, ενημερώνουμε το αντίστοιχο πεδίο
        if row_id != new_primary_key_value: 
            cursor.execute(f"UPDATE {table_name} SET {primary_key_column} = ? WHERE {primary_key_column} = ?", (new_primary_key_value, row_id))
        
        conn.commit()
        
        messagebox.showinfo("Επιτυχία ✔", "Τα δεδομένα ενημερώθηκαν επιτυχώς!")
        show_table_data(table_name, treeview, conn, cursor)

    except sqlite3.Error as e:
        messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την ενημέρωση: {e}")

def delete_selected_row(selected_item, treeview, conn, cursor):
    if not selected_item:
        messagebox.showerror("Σφάλμα", "Δεν έχει επιλεγεί καμία γραμμή!")
        return

    table_name = treeview.item(selected_item)["tags"]
    if not table_name:
        messagebox.showerror("Σφάλμα", "Δεν είναι διαθέσιμο το όνομα του πίνακα!")
        return

    table_name = table_name[0]

    row_data = treeview.item(selected_item)["values"]

    # Ανίχνευση της στήλης του πρωτεύοντος κλειδιού
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    primary_key_column = None
    for col_info in columns_info:
        if col_info[5] == 1:  # Το πεδίο 'pk' είναι 1 για την στήλη του πρωτεύοντος κλειδιού
            primary_key_column = col_info[1]
            break

    if primary_key_column is None:
        messagebox.showerror("Σφάλμα", "Δεν βρέθηκε πρωτεύων κλειδί για τον πίνακα!")
        return

    primary_key_value = row_data[treeview["columns"].index(primary_key_column)]

    confirm = messagebox.askyesno("Επιβεβαίωση Διαγραφής", "Είστε σίγουροι ότι θέλετε να διαγράψετε αυτή την εγγραφή;")
    if not confirm:
        return

    try:
        cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key_column} = ?", (primary_key_value,))
        conn.commit()
        show_table_data(table_name, treeview, conn, cursor)

        # Δημιουργία παραθύρου επιτυχίας
        success_window = tk.Toplevel()
        success_window.title("Επιτυχία")
        #success_window.geometry("250x170")
        success_window.configure(bg="#DFF2BF")
       
        window_width = 250
        window_height = 170
 
        # Calculate the screen width and height
        screen_width = success_window.winfo_screenwidth()
        screen_height = success_window.winfo_screenheight()

       # Calculate the position for the window to be centered
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)

    # Set the geometry of the Toplevel window
        success_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")


        label_tick = tk.Label(success_window, text="✔", font=("Arial", 24), fg="green", bg="#DFF2BF")
        label_tick.pack(pady=10)

        label_message = tk.Label(success_window, text="Η εγγραφή διαγράφηκε επιτυχώς!", font=("Arial", 11), bg="#DFF2BF")
        label_message.pack(pady=10)

        # Δημιουργία μικρού, κομψού κουμπιού ΟΚ
        ok_button = tk.Button(
            success_window,
            text="ΟΚ",
            font=("Helvetica", 10, "bold"),
            fg="white",
            bg="#4CAF50",
            activebackground="#45a049",
            activeforeground="white",
            bd=0,  # Χωρίς περίγραμμα
            width=6,
            height=1,  # Μικρό μέγεθος
            relief="flat",  # Στυλ επίπεδου κουμπιού
            command=success_window.destroy
        )
        ok_button.pack(pady=10)

    except sqlite3.Error as e:
        messagebox.showerror("Σφάλμα", f"Αποτυχία διαγραφής της γραμμής: {e}")


def create_context_menu(treeview, conn, cursor):
    menu = tk.Menu(treeview, tearoff=0)
    menu.add_command(label="UPDATE", command=lambda: update_selected_row(treeview.selection()[0], treeview, conn, cursor))
    menu.add_command(label="DELETE", command=lambda: delete_selected_row(treeview.selection()[0], treeview, conn, cursor))

    def show_context_menu(event):
        selected_item = treeview.identify_row(event.y)
        if selected_item:
            treeview.selection_set(selected_item)
            menu.post(event.x_root, event.y_root)

    treeview.bind("<Button-3>", show_context_menu)

def open_faq_window(previous_window):
    previous_window.destroy()

    faq_window = tk.Toplevel()
    faq_window.title("Συχνές Ερωτήσεις")
    #faq_window.geometry("800x600")
    
    window_width = 900
    window_height = 600
 
    # Calculate the screen width and height
    screen_width = faq_window.winfo_screenwidth()
    screen_height = faq_window.winfo_screenheight()

    # Calculate the position for the window to be centered
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height //2) - (window_height // 2)

    faq_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    

    faq_window.configure(bg="#B0E0E6")

    # Ερώτηση με Bag Tag
    label = tk.Label(faq_window, text="Εύρεση επιβάτη με βάση το bag tag :", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label.pack(pady=15, padx=20, fill='x')

    frame_input = tk.Frame(faq_window, bg="#B0E0E6")
    frame_input.pack(pady=5, padx=20, fill='x')

    label_bag_tag = tk.Label(frame_input, text="Bag Tag:", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label_bag_tag.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    entry_bag_tag = tk.Entry(frame_input, font=("Arial", 12))
    entry_bag_tag.grid(row=0, column=1, padx=10, pady=5)

    def search_passenger_by_bag_tag():
        bag_tag = entry_bag_tag.get().strip()
        if not bag_tag:
            messagebox.showerror("Σφάλμα", "Παρακαλώ εισάγετε έναν αριθμό bag tag.")
            return

        conn, cursor = connect_to_db()
        if not conn or not cursor:
            return

        try:
            query = """
                SELECT e.AFM, e.onoma
                FROM BAG_TAG as b
                JOIN EISHTHRIO as t ON b.kod_eishthriou = t.kod_eishthriou
                JOIN EPIVATHS as e ON t.AFM = e.AFM
                WHERE b.kod_bag_tag = ?
            """
            cursor.execute(query, (bag_tag,))
            result = cursor.fetchall()

            if result:
                results_text = "\n".join([f"AFM: {row[0]}, Όνομα: {row[1]}" for row in result])
                messagebox.showinfo("Αποτέλεσμα", results_text)
            else:
                messagebox.showinfo("Αποτέλεσμα", "Δεν βρέθηκε επιβάτης με το συγκεκριμένο bag tag.")

        except sqlite3.Error as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εκτέλεση της ερώτησης: {e}")
        finally:
            conn.close()

    search_button = tk.Button(frame_input, text="Αναζήτηση", font=("Arial", 12), command=search_passenger_by_bag_tag)
    search_button.grid(row=0, column=2, padx=10, pady=5)

    # Ερώτηση για τον κωδικό εγγράφου ταυτοποίησης
    label2 = tk.Label(faq_window, text="Εύρεση πτήσης επιβάτη με βάση τον κωδικό εγγράφου ταυτοποίησης :", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label2.pack(pady=15, padx=20, fill='x')

    frame_input2 = tk.Frame(faq_window, bg="#B0E0E6")
    frame_input2.pack(pady=5, padx=20, fill='x')

    label_doc_id = tk.Label(frame_input2, text="Κωδικός Εγγράφου:", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label_doc_id.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    entry_doc_id = tk.Entry(frame_input2, font=("Arial", 12))
    entry_doc_id.grid(row=0, column=1, padx=10, pady=5)

    def search_flight_by_doc_id():
        doc_id = entry_doc_id.get().strip()
        if not doc_id:
            messagebox.showerror("Σφάλμα", "Παρακαλώ εισάγετε έναν κωδικό εγγράφου.")
            return

        conn, cursor = connect_to_db()
        if not conn or not cursor:
            return

        try:
            query = """
                SELECT e.kod_pthshs
                FROM EPIVATHS as e
                JOIN EGGRAFO_TAYTOPOIHSHS as g ON e.AFM = g.AFM
                WHERE g.kod_taytopoihshs = ?
            """
            cursor.execute(query, (doc_id,))
            result = cursor.fetchall()

            if result:
                results_text = "\n".join([f"Κωδικός Πτήσης: {row[0]}" for row in result])
                messagebox.showinfo("Αποτέλεσμα", results_text)
            else:
                messagebox.showinfo("Αποτέλεσμα", "Δεν βρέθηκε πτήση για τον συγκεκριμένο κωδικό εγγράφου.")

        except sqlite3.Error as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εκτέλεση της ερώτησης: {e}")
        finally:
            conn.close()

    search_button2 = tk.Button(frame_input2, text="Αναζήτηση", font=("Arial", 12), command=search_flight_by_doc_id)
    search_button2.grid(row=0, column=2, padx=10, pady=5)

    # Ερώτηση για καθυστέρηση αναχώρησης πτήσης
    label3 = tk.Label(faq_window, text="Υπολογισμός χρονικής καθυστέρησης πτήσης αναχώρησης :", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label3.pack(pady=15, padx=20, fill='x')

    frame_input3 = tk.Frame(faq_window, bg="#B0E0E6")
    frame_input3.pack(pady=5, padx=20, fill='x')

    label_flight_code = tk.Label(frame_input3, text="Κωδικός Πτήσης:", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label_flight_code.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    entry_flight_code = tk.Entry(frame_input3, font=("Arial", 12))
    entry_flight_code.grid(row=0, column=1, padx=10, pady=5)

    def search_flight_delay():
        flight_code = entry_flight_code.get().strip()
        if not flight_code:
            messagebox.showerror("Σφάλμα", "Παρακαλώ εισάγετε έναν κωδικό πτήσης.")
            return

        conn, cursor = connect_to_db()
        if not conn or not cursor:
            return

        try:
            query = """
                SELECT DISTINCT p.kod_pthshs, ((julianday(p.pragm_hmer_ora) - julianday(e.hmer_ora_anax)) * 24 * 60 ) AS difference_in_minutes
                FROM PTHSH AS p
                JOIN EISHTHRIO AS e ON p.kod_pthshs = e.kod_pthshs
                WHERE p.kod_pthshs = ?
            """
            cursor.execute(query, (flight_code,))
            result = cursor.fetchall()

            if result:
                results_text = "\n".join([f"Κωδικός Πτήσης: {row[0]}, Καθυστέρηση: {row[1]:.2f} λεπτά" for row in result])
                messagebox.showinfo("Αποτέλεσμα", results_text)
            else:
                messagebox.showinfo("Αποτέλεσμα", "Δεν βρέθηκε καθυστέρηση για την πτήση με τον συγκεκριμένο κωδικό.")

        except sqlite3.Error as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εκτέλεση της ερώτησης: {e}")
        finally:
            conn.close()

    search_button3 = tk.Button(frame_input3, text="Αναζήτηση", font=("Arial", 12), command=search_flight_delay)
    search_button3.grid(row=0, column=2, padx=10, pady=5)

    # Ερώτηση για επιπλέον βάρος αποσκευής και χρέωση
    label4 = tk.Label(faq_window, text="Εύρεση επιπλέον βάρους αποσκευής και υπολογισμός πρόσθετης χρέωσης με βάση το ΑΦΜ :", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label4.pack(pady=15, padx=20, fill='x')

    frame_input4 = tk.Frame(faq_window, bg="#B0E0E6")
    frame_input4.pack(pady=5, padx=20, fill='x')

    label_afm = tk.Label(frame_input4, text="ΑΦΜ:", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label_afm.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    entry_afm = tk.Entry(frame_input4, font=("Arial", 12))
    entry_afm.grid(row=0, column=1, padx=10, pady=5)

    def search_extra_baggage_and_charge():
        afm = entry_afm.get().strip()
        if not afm:
            messagebox.showerror("Σφάλμα", "Παρακαλώ εισάγετε έναν ΑΦΜ.")
            return

        conn, cursor = connect_to_db()
        if not conn or not cursor:
            return

        try:
            query = """
                SELECT a.pragmatiko_varos - s.epitr_varos AS epipl_kila, a.teliki_xreosi
                FROM APOSKEVI AS a
                JOIN EPIVATHS AS e ON e.AFM = a.AFM
                JOIN EISHTHRIO AS s ON e.AFM = s.AFM
                WHERE a.AFM = ?
            """
            cursor.execute(query, (afm,))
            result = cursor.fetchall()

            if result:
                results_text = "\n".join([f"Επιπλέον Κιλά: {row[0]:.2f}, Τελική Χρέωση: {row[1]:.2f} ευρώ" for row in result])
                messagebox.showinfo("Αποτέλεσμα", results_text)
            else:
                messagebox.showinfo("Αποτέλεσμα", "Δεν βρέθηκαν στοιχεία για τον επιβάτη με τον συγκεκριμένο ΑΦΜ.")

        except sqlite3.Error as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εκτέλεση της ερώτησης: {e}")
        finally:
            conn.close()

    search_button4 = tk.Button(frame_input4, text="Αναζήτηση", font=("Arial", 12), command=search_extra_baggage_and_charge)
    search_button4.grid(row=0, column=2, padx=10, pady=5)

    # Ερώτηση για πυλή επιβίβασης
    label5 = tk.Label(faq_window, text="Εύρεση πύλης επιβίβασης με βάση τον κωδικό της πτήσης :", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label5.pack(pady=15, padx=20, fill='x')

    frame_input5 = tk.Frame(faq_window, bg="#B0E0E6")
    frame_input5.pack(pady=5, padx=20, fill='x')

    label_flight_code2 = tk.Label(frame_input5, text="Κωδικός Πτήσης:", font=("Arial", 12), bg="#B0E0E6", anchor="w")
    label_flight_code2.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    entry_flight_code2 = tk.Entry(frame_input5, font=("Arial", 12))
    entry_flight_code2.grid(row=0, column=1, padx=10, pady=5)

    def search_gate_of_flight():
        flight_code = entry_flight_code2.get().strip()
        if not flight_code:
            messagebox.showerror("Σφάλμα", "Παρακαλώ εισάγετε έναν κωδικό πτήσης.")
            return

        conn, cursor = connect_to_db()
        if not conn or not cursor:
            return

        try:
            query = """
                SELECT DISTINCT arithmos_pylhs
                FROM EPIVIVASH
                WHERE kod_pthshs = ?
            """
            cursor.execute(query, (flight_code,))
            result = cursor.fetchall()

            if result:
                results_text = "\n".join([f"Πυλή: {row[0]}" for row in result])
                messagebox.showinfo("Αποτέλεσμα", results_text)
            else:
                messagebox.showinfo("Αποτέλεσμα", "Δεν βρέθηκαν πυλές επιβίβασης για την πτήση με τον συγκεκριμένο κωδικό.")

        except sqlite3.Error as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα κατά την εκτέλεση της ερώτησης: {e}")
        finally:
            conn.close()

    search_button5 = tk.Button(frame_input5, text="Αναζήτηση", font=("Arial", 12), command=search_gate_of_flight)
    search_button5.grid(row=0, column=2, padx=10, pady=5)

    def on_closing():
        open_next_window()
        faq_window.destroy()

    faq_window.protocol("WM_DELETE_WINDOW", on_closing)



def open_statistics_window(previous_window):
    previous_window.destroy()

    stats_window = tk.Toplevel()
    stats_window.title("Στατιστικά")
    #stats_window.geometry("1000x600")
    window_width = 900
    window_height = 600
 
    # Calculate the screen width and height
    screen_width = stats_window.winfo_screenwidth()
    screen_height = stats_window.winfo_screenheight()

    # Calculate the position for the window to be centered
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)

    stats_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    stats_window.configure(bg="#B0E0E6")


    # Δημιουργία του Combobox με τις 7 ερωτήσεις
    questions = [
        "Αριθμός επιβατών ανά εταιρία",
        "Αριθμός επιβατών ανά προορισμό",
        "Αριθμός αφικνούμενων πτήσεων ανά αεροδρόμιο προέλευσης",
        "Μέσο βάρος αποσκευής ανά πτήση",
        "Αριθμός εξυπηρετηθέντων επιβατών ανά υπάλληλο check in",
        "Αριθμός επιβάτων ανά κατηγορία θέσης ανά πτήση",
        "Πληρότητα ανά πτήση"
    ]

    # Ετικέτα για την επιλογή ερώτησης
    combobox_label = tk.Label(stats_window, text="Επιλέξτε μια ερώτηση:", font=("Arial", 12), bg="#B0E0E6")
    combobox_label.pack(pady=10)

    # Combobox για τις ερωτήσεις
    combobox = ttk.Combobox(stats_window, values=questions, font=("Arial", 12), width=50)
    combobox.pack(pady=10)
    
    # Ετικέτα για τα αποτελέσματα
    results_label = tk.Label(stats_window, text="Αποτελέσματα:", font=("Arial", 12), bg="#B0E0E6")
    results_label.pack(pady=10)


    # Πεδίο κειμένου για εμφάνιση αποτελεσμάτων
    results_text = tk.Text(stats_window, width=80, height=20, font=("Arial", 12))
    results_text.pack(pady=10)

    # Σύνδεση του combobox με τη συνάρτηση on_combobox_select
    combobox.bind("<<ComboboxSelected>>", lambda event: on_combobox_select(event, combobox,results_text))

    def on_closing():
        open_next_window()
        stats_window.destroy()

    stats_window.protocol("WM_DELETE_WINDOW", on_closing)

    stats_window.mainloop()

def get_query_result(query):
    """Εκτέλεση SQL query και επιστροφή των αποτελεσμάτων"""
    conn = sqlite3.connect('AERODROMIO_FINAL.db')  # Σύνδεση με τη βάση δεδομένων (προσαρμόστε το path της DB σας)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def display_results(results,results_text):

    """Εμφάνιση των αποτελεσμάτων στην GUI"""
    results_text.delete(1.0, tk.END)  # Καθαρίζει το προηγούμενο κείμενο
    # Προσθήκη του Scrollbar
    for result in results:
        results_text.insert(tk.END, str(result) + "\n")

def on_combobox_select(event,combobox, results_text):
    """Εκτέλεση του κατάλληλου query ανάλογα με την επιλογή"""
    #global combobox
    selected_question = combobox.get()
    
    if selected_question == "Αριθμός επιβατών ανά εταιρία":
        query = '''select a.aerop_etairia,count(e.AFM)  || ' επιβάτες' as ar_epiv 
        from AEROPLANO as a join PTHSH as p on a.kod_aeroplanou=p.kod_aeroplanou join EPIVATHS as e on e.kod_pthshs=p.kod_pthshs
        group by a.aerop_etairia
        order by ar_epiv desc'''
    elif selected_question == "Αριθμός επιβατών ανά προορισμό":
        query = '''select a.poli,count(e.AFM)  || ' επιβάτες' as ar_epiv
        from AERODROMIO as a join PTHSH as p on a.kod_aerodromiou=p.kod_aerodromiou join EPIVATHS as e on e.kod_pthshs=p.kod_pthshs
        where p.eidos='Αναχώρηση' 
        group by a.poli 
        order by ar_epiv desc '''
    elif selected_question == "Αριθμός αφικνούμενων πτήσεων ανά αεροδρόμιο προέλευσης":
        query = '''select a.kod_aerodromiou,count(p.kod_pthshs)  || ' πτήση/εις' as arithmos
        from AERODROMIO as a join PTHSH as p on a.kod_aerodromiou=p.kod_aerodromiou
        where p.eidos='Άφιξη'
        group by a.kod_aerodromiou
        order by arithmos desc'''
    elif selected_question == "Μέσο βάρος αποσκευής ανά πτήση":
        query = '''select e.kod_pthshs,  ROUND(AVG(a.pragmatiko_varos), 1) || ' kg' as avg 
        from APOSKEVI as a join epivaths as e on a.AFM=e.AFM join pthsh as p on p.kod_pthshs=e.kod_pthshs
        group by p.kod_pthshs
        order by p.kod_pthshs'''
    elif selected_question == "Αριθμός εξυπηρετηθέντων επιβατών ανά υπάλληλο check in":
        query = '''select yp.onoma,e.kod_ypal_check_in, count(e.afm) || ' επιβάτες'
        from ((EISHTHRIO as e join YPAL_CHECK_IN as y on e.kod_ypal_check_in=y.kod_ypal_check_in) join YPALLHLOS as YP on y.kod_ypal_check_in=yp.kod_ypal)
        group by e.kod_ypal_check_in'''
    elif selected_question == "Αριθμός επιβάτων ανά κατηγορία θέσης ανά πτήση":
        query = '''select a.aerop_etairia,e.kathg_thesis,count(e.AFM) || ' επιβάτες'
        from EISHTHRIO as e join PTHSH as p on e.kod_pthshs=p.kod_pthshs join AEROPLANO as a on a.kod_aeroplanou=p.kod_aeroplanou
        group by a.aerop_etairia,kathg_thesis
        order by a.aerop_etairia'''
    elif selected_question == "Πληρότητα ανά πτήση":
        query = '''select e.kod_pthshs, count(e.afm),ROUND(CAST(COUNT(e.afm)*100 AS FLOAT) / CAST(a.xoritikothta AS FLOAT), 1) || ' %' as pososto_plirothtas
        from epivaths as e join pthsh as p on e.kod_pthshs=p.kod_pthshs join AEROPLANO as a on a.kod_aeroplanou=p.kod_aeroplanou
        group by e.kod_pthshs
        order by pososto_plirothtas DESC '''
    
    # Εκτέλεση του query και εμφάνιση των αποτελεσμάτων
    results = get_query_result(query)
    display_results(results,results_text)

# Δημιουργία παραθύρου για το κύριο μενού
def open_next_window():
    root.withdraw()

    next_window = tk.Toplevel()
    next_window.title("Κύριο Παράθυρο")
    window_width = 900
    window_height = 600
 
    # Calculate the screen width and height
    screen_width = next_window.winfo_screenwidth()
    screen_height = next_window.winfo_screenheight()

    # Calculate the position for the window to be centered
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)
    #root.geometry("800x600")
    next_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    #next_window.geometry("800x600")
    next_window.configure(bg="#B0E0E6")
       
    frame = tk.Frame(next_window, bg="#B0E0E6")
    frame.pack(padx=20, pady=20, expand=True)

    btn_data_management = tk.Button(frame, text="Προβολή και Διαχείριση Δεδομένων", font=("Arial", 14),
                                    command=lambda: open_data_management_window(next_window),width=30)
    btn_data_management.pack(pady=12)
    btn_faq = tk.Button(frame, text="Συχνές Ερωτήσεις", font=("Arial", 14),
                        command=lambda: open_faq_window(next_window), width=30)
    btn_faq.pack(pady=12)

    btn_statistics = tk.Button(frame, text="Στατιστικά", font=("Arial", 14),
                               command=lambda: open_statistics_window(next_window), width=30)
    btn_statistics.pack(pady=12)

    def on_closing():
        root.deiconify()
        next_window.destroy()

    next_window.protocol("WM_DELETE_WINDOW", on_closing)


def open_data_management_window(previous_window):
    previous_window.destroy()

    data_window = tk.Toplevel()
    data_window.title("Προβολή και Διαχείριση Δεδομένων")
    window_width = 900
    window_height = 600
 
    # Calculate the screen width and height
    screen_width = data_window.winfo_screenwidth()
    screen_height = data_window.winfo_screenheight()

    # Calculate the position for the window to be centered
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)

    data_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    
    #data_window.geometry("900x600")
    data_window.configure(bg='#ADD8E6')

    conn, cursor = connect_to_db()
    if not conn or not cursor:
        return

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            
            tk.Label(data_window, text="Δεν υπάρχουν πίνακες στη βάση.", font=("Arial", 14), bg="#ADD8E6").pack(pady=10)
            return

        canvas = tk.Canvas(data_window, height=30)
        frame_tables = tk.Frame(canvas, bg='#ADD8E6', height='70')
        scrollbar_x = ttk.Scrollbar(data_window, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=scrollbar_x.set, bg='#ADD8E6')

        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.TOP, fill=tk.X, padx=15)
        canvas.create_window((0, 0), window=frame_tables, anchor="nw")

        buttons = []
        for table in tables:
            btn = tk.Button(frame_tables, text=table, font=("Arial", 10), width=15,
                            command=lambda t=table: show_table_data(t, treeview, conn, cursor))
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            buttons.append(btn)

        frame_tables.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        frame_data = tk.Frame(data_window, bg="#ADD8E6")
        frame_data.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)

        treeview_scrollbar_y = ttk.Scrollbar(frame_data, orient="vertical")
        treeview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        treeview = ttk.Treeview(frame_data, yscrollcommand=treeview_scrollbar_y.set)
        treeview.pack(fill=tk.BOTH, expand=True)

        treeview_scrollbar_y.config(command=treeview.yview)

        create_context_menu(treeview, conn, cursor)

        if tables:
            show_table_data(tables[0], treeview, conn, cursor)

    except sqlite3.Error as e:
        messagebox.showerror("Σφάλμα", f"Δεν είναι δυνατή η ανάκτηση πινάκων: {e}")

    def on_closing():
        conn.close()
        open_next_window()
        data_window.destroy()
    data_window.protocol("WM_DELETE_WINDOW", on_closing)

# Δημιουργία παραθύρου σύνδεσης
root = tk.Tk()
root.title("Σύνδεση")
window_width = 900
window_height = 600
 
# Calculate the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the position for the window to be centered
x_position = (screen_width // 2) - (window_width // 2)
y_position = (screen_height // 2) - (window_height // 2)
#root.geometry("800x600")
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

root.configure(bg="#ADD8E6")


# Εισαγωγή εικόνας background
background_image = tk.PhotoImage(file="AEROPLANO_DB.png")  # Βάλτε το όνομα της εικόνας εδώ
background_label = tk.Label(root, image=background_image)
background_label.place(relwidth=1, relheight=1)

# Δημιουργία κουμπιών εισόδου
frame = tk.Frame(root, bd=5)
#frame.place(relx=0.5, rely=0.5, anchor="center")
frame.place( relx=0.5, rely=0.1,anchor="n")

label_username = tk.Label(frame, text="Username:", font=("Arial", 12))
label_username.grid(row=0, column=0, padx=10, pady=5)
entry_username = tk.Entry(frame, font=("Arial", 12))
entry_username.grid(row=0, column=1, padx=10, pady=5)

label_password = tk.Label(frame, text="Password:", font=("Arial", 12))
label_password.grid(row=1, column=0, padx=10, pady=5)
entry_password = tk.Entry(frame, font=("Arial", 12), show="*")
entry_password.grid(row=1, column=1, padx=10, pady=5)

login_button = tk.Button(frame, text="Σύνδεση", font=("Arial", 12), command=check_login)
login_button.grid(row=2, columnspan=2, pady=10)

root.mainloop()
