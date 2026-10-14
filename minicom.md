# Minicom 

```c
sudo apt update
sudo apt-get install minicom
```

- Önce bu komutları çalıştır ki <b>```minicom```</b>'u kurabilelim. 

<b>```Minicom```</b> bir seri port terminal programıdır.

- Daha sonra <b> ```USB TO UART (USB-TTL)```</b> dönüştürücünü bilgisayara bağla. 


Terminal şu komutu çalıştır:

```c
dmesg | grep tty
```
-Bu komutu yazınca aşağıdaki gibi bir çıktı vermesi gerekiyor. 

![alt text](images/{D08296A2-927C-4477-88AA-80FA9DC1250A}.png)

- Dönüştürücünün kullandığı çipi algılaması gerekiyor. (Burada illa <b>```pl2303```</b> yazması gerekmiyor. <b>```cp210x```</b> de yazabilirdi.)


- Bizim burada <b>```ttyUSB0```</b> <b>Minicom</b>'da kullancağımız portun adı ( <b>/dev/ttyUSB0</b> )

<br>
- Şimdi bu minicom'da gerekli config ayarlarını yapacağımzı arayüze erişme komutunu yazalım.

```c
 sudo minicom -s
```

- Bu komutun çıktısı olarak aşağıdaki ekran gelmeli terminalde.
- Yön tuşları ile bu ekranda gezinebilirsin. Burada <b>```Serial port setup```</b>'ı seçiyoruz.

![alt text](images/{F27FC9A5-A70D-479E-9FE1-A48AF82142C0}.png)

- Daha sonra böyle bir ekran gelecek. Bu ekranda seri port ile ilgili ayarları değiştirebiliriz.

![alt text](images/{46E1CB74-A6AC-4373-91BD-4DC1CC8E5EF1}.png)

- Örneğin ben <b>```Serial Device```</b> adını değiştirmek istiyorum. Burada klavyeden <b>A</b> harfine basacağım ve imleç yer değiştirecek.

![alt text](images/{230FE2DE-7BE6-49B2-B01E-2F294C2C15FE}.png)

- Daha sonra istersem burayı silip yeni bir şey yazabilirim. Değişikil yaptıktan sonra <b>Enter</b>'a bas.

- Örneğin ben <b>Baudrate</b> hızı değiştirmek istiyorum. O zaman klavyeden <b>E</b> tuşuna basacağım. Burada bizi yeni bir arayüze yönlendiriyor.

![alt text](images/{D297BD35-EB7C-4410-B431-A8B84BC48A9D}.png)

- Diyelim ben <b>Baudrate</b> hızını <b>38400</b> yapmak istiyorum. O zaman klavyeden <b>D</b> tuşuna basıyorum ve ilgili ayar arayüzde değişiyor.

![alt text](images/{E3A60A5C-888D-4802-8A22-C1E6AC50C300}.png)

- Bu tarz değişiklikleri arayüzde o config ayarını değiştirmek için hangi kısayolu kullanıcak ise ona basarak gerekli ayarlamaları yapabiliyoruz.

> [!NOTE]
> <b>Beaglebone Black</b> kartında seri haberleşme için <b>CTS</b> ve <b>RTS</b> pinleri yoktur. Bu yüzden <b>Hardware Flow Control</b> kullanamıyor. Bu ayar hep <b>No</b> olarak kalsın. Aynı şekilde <b>Software Flow Control</b> da <b>No</b> olarak kalsın.

- Config işlemleri tamamlandıktan sonra en baştaki arayüze dönerek <b>```Save setup as dfl```</b> seçeneği seçiyoruz. Çünkü bu yaptığımız ayarları default olarak kaydedilsin ki sürekli bu ayarlamları yapmak zorunda kalmayalım. Daha sonra <b>Exit</b>'i seçerek çıkış yapabilirsin.

![alt text](images/{25B687AC-C882-4EAD-82C6-B4EA24B58170}.png)
