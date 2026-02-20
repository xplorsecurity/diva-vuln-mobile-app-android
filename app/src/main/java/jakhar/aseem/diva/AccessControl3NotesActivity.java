```java
package jakhar.aseem.diva;

import android.content.ContentResolver;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.SimpleCursorAdapter;
import android.widget.TextView;
import android.widget.Toast;

public class AccessControl3NotesActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_access_control3_notes);
    }

    public void accessNotes(View view) {
        EditText pinTxt = (EditText) findViewById(R.id.aci3notesPinText);
        Button abutton = (Button) findViewById(R.id.aci3naccessbutton);
        SharedPreferences spref = PreferenceManager.getDefaultSharedPreferences(this);
        String pin = spref.getString(getString(R.string.pkey), "");
        String userpin = pinTxt.getText().toString();

        // XXX Easter Egg?
        if (userpin.equals(pin)) {
            // Display the private notes
            ListView lview = (ListView) findViewById(R.id.aci3nlistView);
            Cursor cr = getContentResolver().query(NotesProvider.CONTENT_URI, new String[] {"_id", "title", "note"}, null, null, null);
            String[] columns = {NotesProvider.C_TITLE, NotesProvider.C_NOTE};
            int[] fields = {R.id.title_entry, R.id.note_entry};
            SimpleCursorAdapter adapter = new SimpleCursorAdapter(this, R.layout.notes_entry, cr, columns, fields, 0);
            lview.setAdapter(adapter);

            // Clear sensitive data before hiding the views
            pinTxt.setText(""); // Clear the text in the EditText
            pinTxt.setVisibility(View.INVISIBLE);
            abutton.setVisibility(View.INVISIBLE);

            if (cr != null) {
                cr.close(); // Close the cursor to release resources
            }
        } else {
            Toast.makeText(this, "Please Enter a valid pin!", Toast.LENGTH_SHORT).show();
        }
    }
}
```