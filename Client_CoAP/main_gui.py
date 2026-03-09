import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import socket
import message as coap


class CoAP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CoAP Client - Remote Storage")
        self.root.geometry("780x820")
        self.root.resizable(False, False)

        tk.Label(self.root, text="Server URI:", font=("Arial", 12)).place(x=170, y=35)
        self.entry_uri = tk.Entry(self.root, font=("Arial", 11), width=50)
        self.entry_uri.place(x=280, y=30)
        self.entry_uri.insert(0, "192.168.1.130")

        tk.Label(self.root, text="Action:", font=("Arial", 12)).place(x=170, y=100)
        self.combo_method = ttk.Combobox(self.root, values=["CREATE", "GET", "DELETE", "MOVE", "EDIT"], state="readonly")
        self.combo_method.place(x=280, y=100, width=160)
        self.combo_method.current(0)

        tk.Label(self.root, text="File Content:", font=("Arial", 12)).place(x=170, y=160)
        self.text_payload = scrolledtext.ScrolledText(self.root, width=52, height=11, font=("Arial", 10))
        self.text_payload.place(x=280, y=160)

        tk.Label(self.root, text="File Name:", font=("Arial", 12)).place(x=90, y=370)
        self.entry_name = tk.Entry(self.root, font=("Arial", 11), width=15)
        self.entry_name.place(x=190, y=370)

        tk.Label(self.root, text="Extension:", font=("Arial", 12)).place(x=90, y=420)
        self.entry_ext = tk.Entry(self.root, font=("Arial", 11), width=15)
        self.entry_ext.place(x=190, y=420)

        tk.Label(self.root, text="New Name:", font=("Arial", 12)).place(x=90, y=470)
        self.entry_newname = tk.Entry(self.root, font=("Arial", 11), width=15)
        self.entry_newname.place(x=190, y=470)

        tk.Label(self.root, text="New Path:", font=("Arial", 12)).place(x=90, y=520)
        self.entry_newpath = tk.Entry(self.root, font=("Arial", 11), width=15)
        self.entry_newpath.place(x=190, y=520)

        self.is_confirmable = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Confirmable (ACK)", var=self.is_confirmable, font=("Arial", 11)).place(x=190,y=570)

        tk.Button(self.root, text="EXECUTE", font=("Arial", 12, "bold"), width=10, command=self.on_send_click,bg="#e1e1e1").place(x=60, y=620)
        tk.Button(self.root, text="CLEAR LOG", font=("Arial", 12, "bold"), width=10, command=self.clear_output).place(x=280, y=620)
        tk.Button(self.root, text="EXIT", font=("Arial", 12, "bold"), width=10, command=self.root.quit).place(x=500,y=620)

        self.output = scrolledtext.ScrolledText(self.root, width=92, height=12, font=("Arial", 10), bg="#f8f8f8")
        self.output.place(x=60, y=670)
        self.output.config(state=tk.DISABLED)

        tk.Label(self.root, text="Remote Explorer:", font=("Arial", 12)).place(x=600, y=100)
        self.dir_list = tk.Listbox(self.root, width=28, height=18, font=("Arial", 10))
        self.dir_list.place(x=600, y=130)
        self.dir_list.bind("<<ListboxSelect>>", self.on_select_item)

        tk.Button(self.root, text="REFRESH LIST", font=("Arial", 11), command=self.on_refresh_click).place(x=600, y=350)

    def clear_output(self):
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)

    def on_send_click(self):
        uri = self.entry_uri.get()
        action = self.combo_method.get()
        full_content = self.text_payload.get("1.0", tk.END).strip()

        CHUNK_SIZE = 2
        text_fragments = coap.fragment_payload(full_content, CHUNK_SIZE)
        total_fragments = len(text_fragments)

        # Mapare conform cerintelor CODE_CREATE=1, GET=2, DELETE=3, MOVE=4, EDIT=5
        code_map = {
            "CREATE": coap.CODE_CREATE,
            "GET": coap.CODE_GET,
            "DELETE": coap.CODE_DELETE,
            "MOVE": coap.CODE_MOVE,
            "EDIT": coap.CODE_EDIT
        }
        current_code = code_map.get(action, coap.CODE_GET)

        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, f">>> Start {action}: {total_fragments} fragments\n")

        for i in range(total_fragments):
            current_index = i + 1
            chunk_text = text_fragments[i]

            payload_dict = {
                "name": self.entry_name.get(),
                "extension": self.entry_ext.get(),
                "f_cur": current_index,
                "f_tot": total_fragments
            }

            if action == "CREATE":
                payload_dict["path"] = ""
                if payload_dict["extension"]:
                    payload_dict["type"] = "file"
                    payload_dict["content"] = chunk_text
                else:
                    payload_dict["type"] = "directory"
            elif action == "GET":
                payload_dict["path"] = f"/{self.entry_name.get()}.{self.entry_ext.get()}"
                payload_dict["content"] = ""
            elif action == "DELETE":
                payload_dict["path"] = f"/{self.entry_name.get()}.{self.entry_ext.get()}"
            elif action == "EDIT":
                payload_dict["path"] = f"{self.entry_name.get()}.{self.entry_ext.get()}"
                payload_dict["new_name"] = self.entry_newname.get()
            elif action == "MOVE":
                payload_dict["path"] = f"/{self.entry_name.get()}.{self.entry_ext.get()}"
                payload_dict["new_path"] = self.entry_newpath.get()

            raw_payload = coap.create_payload(**payload_dict)
            msg = coap.message_init(token=b'\x01', payload=raw_payload)
            msg["code"] = current_code
            msg["type"] = coap.TYPE_CONFIRMABLE if self.is_confirmable.get() else coap.TYPE_NONCONFIRMABLE

            try:
                packet = coap.encode_message(msg)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('0.0.0.0', 6000))
                sock.settimeout(2)
                sock.sendto(packet, (uri, 5000))

                try:
                    resp_data, addr = sock.recvfrom(4096)
                    resp_msg = coap.decode_message(resp_data)
                    self.output.insert(tk.END, f"  [Part {current_index}/{total_fragments}] ACK Received, {resp_msg}\n")
                except socket.timeout:
                    self.output.insert(tk.END, f"  [Part {current_index}/{total_fragments}] Sent (No ACK)\n")
                finally:
                    sock.close()
            except Exception as e:
                self.output.insert(tk.END, f"  Network Error: {str(e)}\n")
                break

        self.output.insert(tk.END, f">>> {action} Finished.\n\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def on_refresh_click(self):
        msg = coap.message_init(token=b'\x02', payload=coap.create_payload(path="", f_cur=1, f_tot=1))
        msg["code"] = coap.CODE_GET

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Permite refolosirea portului
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', 6000))
            
            sock.settimeout(2)
            sock.sendto(coap.encode_message(msg), (self.entry_uri.get(), 5000))

            resp, _ = sock.recvfrom(4096)
            data = coap.decode_message(resp)["payload"].decode("utf-8", "ignore")

            try:
                entries = json.loads(data)
            except:
                data = data.replace("[", "").replace("]", "").replace("'", "")
                entries = data.split(", ")

            self.dir_list.delete(0, tk.END)
            for e in entries:
                if e.strip():
                    self.dir_list.insert(tk.END, e.strip())
        except Exception as e:
            messagebox.showerror("Refresh Error", str(e))
        finally:
            sock.close()
    
    def on_select_item(self, event):
        selection = event.widget.curselection()
        if selection:
            val = event.widget.get(selection[0])
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, val.split(".")[0])
            if "." in val:
                self.entry_ext.delete(0, tk.END)
                self.entry_ext.insert(0, val.split(".")[1])


if __name__ == "__main__":
    root = tk.Tk()
    app = CoAP_GUI(root)
    root.mainloop()
