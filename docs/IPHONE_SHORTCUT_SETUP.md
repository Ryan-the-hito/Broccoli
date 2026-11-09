# Ask Broccoli from your iPhone

<p><a href="IPHONE_SHORTCUT_SETUP_zh.md">简体中文</a> · <b>English</b> · <a href="IPHONE_SHORTCUT_SETUP_ja.md">日本語</a></p>

This guide sets up one Shortcut, called **Broccoli**, on your iPhone. Each time you run it, it does three things:

1. Asks which Mac should answer.
2. Asks whether to start a new conversation or continue one of that Mac's 30 most recent conversations.
3. Asks for your question.

The Mac answers. The answer appears in the **Notes** app, in a folder called **Broccoli**, and a reminder goes off on your iPhone when it is ready.

The Shortcut only reads and writes the Shortcuts app's own iCloud folder. It contains no names or device codes, so you can share it with anyone as a link.

## What you need

- At least one Mac running Broccoli (this version or later).
- The iPhone and the Mac signed in to the **same Apple Account**, with **iCloud Drive** turned on for both.
- iOS 18 or later on the iPhone, for Step 0.
- In Broccoli's Settings, under **iCloud remote tasks**, the switch **Apple Notes mirror + iPhone Shortcuts** turned on. It is on by default.

## Before you start: on each Mac

1. Quit Broccoli and open it again.
2. Wait about 15 seconds. Broccoli creates a folder called **Broccoli** inside the Shortcuts app's iCloud folder.

Do this on every Mac you want to choose from the iPhone. A Mac running an older version of Broccoli does not appear in the list.

## Step 0: keep the Broccoli folder downloaded on the iPhone

iCloud sometimes shows a file on the iPhone without downloading it. When that happens, the Shortcut cannot read the file and stops with an error. Turn this setting on once, and iCloud keeps the folder's files on the iPhone, including the ones a Mac updates later.

1. Open the **Files** app and tap **Browse**.
2. Tap **iCloud Drive**, then **Shortcuts**.
3. Check that a **Broccoli** folder is there. If it is not, wait a minute for iCloud to sync. If it still does not appear, go back to "Before you start".
4. **Touch and hold** the **Broccoli** folder. Do not open it.
5. Tap **Keep Downloaded**. The next time you touch and hold the folder, the option has a check mark.

The folder holds only a few small text files, so this uses almost no storage.

## Build the Shortcut

Add each action from the search field at the bottom of the editor (**Search Actions**). In the steps below, a "box" is a blue field inside an action. Tap a box to change it.

> **Watch for auto-filled boxes.** When you add an action, Shortcuts often fills its first box with the result of the action above it. If a box shows something other than what a step says, tap it and choose **Clear Variable**, then set it as described.

1. Open **Shortcuts**, tap the **Shortcuts** tab, then tap **+** in the top-right corner.
2. Tap the name at the top, tap **Rename**, and type `Broccoli`.

**Choose the Mac**

3. Add **Get File from Folder**. It reads **Get file from [Shortcuts] at path [path]**.
   - The first box should say **Shortcuts**. If it is empty, tap it, choose **iCloud Drive › Shortcuts**, and tap **Open**.
   - Tap the **path** box and type `Broccoli/Macs.txt`.
4. Add **Split Text**. It should read **Split [File] by [New Lines]**.
5. Add **Choose from List**. Tap the small arrow to expand it, and type `Which Mac?` as the **Prompt**.
6. Add **Set Variable**. Type `Mac` as the **Variable Name**. Its value should be **Chosen Item**.

**Choose the conversation**

7. Add **Get File from Folder** again.
   - The first box is probably auto-filled with **Mac**. Tap it, choose **Clear Variable**, and make sure it says **Shortcuts**, as in step 3.
   - Tap the **path** box. Type `Broccoli/Lists/`, including the final slash. Then tap **Mac** in the variable bar above the keyboard. If **Mac** is not there, tap **Select Variable** and choose **Mac**. Then type `.txt`.
   - The box now reads: `Broccoli/Lists/` **Mac** `.txt`
8. Add **Split Text**. Its first box must be the **File** from step 7, and it should split by **New Lines**.
9. Add **Choose from List**, and type `Which conversation?` as the **Prompt**.
10. Add **Set Variable**. Type `Chat` as the **Variable Name**. Its value should be the **Chosen Item** from step 9.

**Ask the question**

11. Add **Ask for Input**. Leave the type as **Text**, and type `What do you want to ask?` as the **Prompt**.
12. Add **Text**. Put exactly three lines in it, with no extra spaces or empty lines:
    - the **Mac** variable
    - the **Chat** variable
    - **Provided Input**

**Save it where the Mac looks**

13. Add **Format Date**.
    - Make the date **Current Date**.
    - Set **Date Format** to **Custom**.
    - Type `yyyyMMdd-HHmmss` as the **Format String**.
14. Add **Set Name**.
    - Tap the first box, tap **Select Variable**, and choose the **Text** from step 12.
    - Tap the **Name** box, insert **Formatted Date**, then type `.txt`.
15. Add **Save File** and expand it.
    - The input should be **Renamed Item**.
    - Turn **Ask Where to Save** off.
    - Leave the folder as **Shortcuts**.
    - Type `Broccoli/Inbox/` as the **Subpath**. You do not need a file name here, because Set Name already provided one.
    - Leave **Overwrite If File Exists** off.
16. Optional: add **Show Notification**, with text such as `Sent to` followed by the **Mac** variable.
17. Tap **Done**.

## Check that it works

1. Run the Shortcut. Choose a Mac, choose **＋ New conversation**, and type a short question.
2. If the iPhone asks whether the Shortcut may access files, choose **Always Allow**.
3. Right away, open **Files › iCloud Drive › Shortcuts › Broccoli › Inbox**.
   - You should see a file named with the date and time, such as `20261031-153000.txt`. That means the save worked.
   - If the Mac is on, the file disappears within a few seconds. That means the Mac picked it up.

## The first time the Mac answers

- The Mac asks whether Broccoli may control **Notes**, and later **Reminders**. Click **OK** both times. If you decline, Broccoli shows a message once that tells you where to change it.
- On the iPhone, allow notifications for Reminders (**Settings › Notifications › Reminders**). Otherwise the reminder will not alert you.

## Everyday use

**The Mac list**

- It shows every Mac that runs this version of Broccoli and has been seen in the last 30 days.
- A Mac that is shut down, asleep or has Broccoli closed is shown as, for example, **MacBook Pro 💤 (offline)**. The mark is in that Mac's own language.
- You can still choose an offline Mac. Your question waits in iCloud and is answered when that Mac is back.

**The conversation list**

- The first line is **＋ New conversation**, shown in the Mac's language.
- Below it are up to 30 of that Mac's most recent conversations, newest first, each shown as `Title · code`. The code tells conversations with the same title apart.
- Choosing a conversation continues it on that Mac, with its earlier context.

**Answers**

- Each answer is a note in **Notes › Broccoli**. The title is the start of your question plus a short code.
- A title starting with ⚠️ means the question was not answered, and the note says why. Your question is kept in the note.
- A title starting with ⏳ means the Mac is waiting for you to approve something. The answer arrives as a separate note.
- About a minute after a note is written, a reminder in the **Broccoli** list in **Reminders** goes off. Reminders are ticked off by themselves a day later.
- To turn the reminders off, use the switch **Remind me on the iPhone when an answer is ready** in Broccoli's Settings, under **iCloud remote tasks**.
- Deleting notes or reminders does not affect anything. The conversations live on the Mac.

## Share it

1. Touch and hold the **Broccoli** Shortcut, then tap **Share › Copy iCloud Link**.
2. Send the link. The other person taps **Add Shortcut**. They do not need to change anything.
3. They need the same things as you: Broccoli on their own Mac and iCloud Drive turned on. They also need to do Step 0 once on their iPhone. Their questions go to their own iCloud and are answered by their own Macs.

## If something looks different or fails

- **The Shortcut stops at step 3 or step 7 with a "file not found" or "doesn't exist" error.**
  - If you skipped Step 0, do it.
  - If your iPhone has no **Keep Downloaded** option, open **Files › iCloud Drive › Shortcuts › Broccoli** and tap `Macs.txt` and the file in **Lists** so they download, then run the Shortcut again.
  - If only step 7 fails, the Mac you chose may run an older Broccoli.
- **The list shows one long item instead of one line per entry.** Add **Get Text from Input** between **Get File from Folder** and **Split Text**, both times.
- **Save File has no Subpath field.** Tap the folder and choose **Shortcuts › Broccoli › Inbox** instead. This works for you, but someone you share the Shortcut with may have to choose the folder again.
- **The file in Inbox is called `Text.txt`.** In step 15, the input must be **Renamed Item**, not **Text**.
- **The file stays in Inbox.** The Mac you chose is off or asleep. The file is answered when that Mac is back.

## Not yet tested on a real iPhone

- The action and option names come from current community documentation and early feedback, and may differ slightly on your iOS version.
- **Keep Downloaded** is documented by Apple for iCloud Drive folders. Two things are not confirmed:
  - that it also downloads files a Mac changes later;
  - that it works on the Shortcuts app's own folder.

  To check, start a new conversation on a Mac so its list changes. After a minute or two, open **Files › … › Broccoli › Lists**. If the files show no cloud icon, they are being downloaded automatically.
