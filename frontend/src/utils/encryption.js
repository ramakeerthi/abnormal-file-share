// Function to generate a random encryption key
export const generateEncryptionKey = async () => {
  const key = await window.crypto.subtle.generateKey(
    {
      name: "AES-GCM",
      length: 256
    },
    true,
    ["encrypt", "decrypt"]
  );
  return key;
};

// Function to export key to base64 string
export const exportKey = async (key) => {
  const exported = await window.crypto.subtle.exportKey("raw", key);
  return btoa(String.fromCharCode(...new Uint8Array(exported)));
};

// Function to import key from base64 string
export const importKey = async (keyStr) => {
  const keyBuffer = Uint8Array.from(atob(keyStr), c => c.charCodeAt(0));
  return await window.crypto.subtle.importKey(
    "raw",
    keyBuffer,
    "AES-GCM",
    true,
    ["encrypt", "decrypt"]
  );
};

// Function to encrypt file
export const encryptFile = async (file) => {
  try {
    console.log('\n=== Client Encryption Started ===');
    console.log('Original file:', {
      name: file.name,
      type: file.type || 'application/octet-stream',
      size: file.size
    });

    const key = await generateEncryptionKey();
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const fileBuffer = await file.arrayBuffer();

    const encryptedContent = await window.crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv: iv
      },
      key,
      fileBuffer
    );

    const encryptedFile = new File(
      [encryptedContent], 
      file.name,
      { type: file.type || 'application/octet-stream' }
    );

    const exportedKey = await exportKey(key);
    const exportedIv = btoa(String.fromCharCode(...iv));

    return {
      encryptedFile,
      key: exportedKey,
      iv: exportedIv
    };
  } catch (error) {
    console.error('Client encryption error:', error);
    throw error;
  }
};

// Function to decrypt file
export const decryptFile = async (encryptedBlob, keyStr, ivStr) => {
  try {
    console.log('\n=== Client Decryption Started ===');
    console.log('Encrypted blob:', {
      size: encryptedBlob.size,
      type: encryptedBlob.type
    });
    console.log('Key length:', keyStr?.length);
    console.log('IV length:', ivStr?.length);

    const key = await importKey(keyStr);
    const iv = Uint8Array.from(atob(ivStr), c => c.charCodeAt(0));
    const encryptedBuffer = await encryptedBlob.arrayBuffer();

    console.log('Encrypted buffer size:', encryptedBuffer.byteLength);

    const decryptedContent = await window.crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: iv
      },
      key,
      encryptedBuffer
    );

    console.log('Decrypted content size:', decryptedContent.byteLength);
    console.log('=== Client Decryption Complete ===\n');

    return new Blob([decryptedContent]);
  } catch (error) {
    console.error('Client decryption error:', error);
    throw error;
  }
}; 