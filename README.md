№№№# Анализатор выгруки Роскомнадзора

Анализатор берёт дамп выгрузки РКН с github, достаёт из него адреса + ресолвит домены.
Результат агрегирует в набор префиксов заданнной длины

### Установка

Для работы нужен python3 и 2 модуля из pip(gevent и requests)

* 
```
git clone https://github.com/pragus/rkn-bl-aggregator.git 
```
* 

```
cd rkn-bl-aggregator
```
*
```
python3 -m pip install -r requirements.txt
```

### Использование

```
Roscomnadzor blacklist aggreation tool.

optional arguments:
  -h, --help  show this help message and exit
  --target    Prefix aggregation target mask length
  --write     Write state file to disk(0 or 1)
  --read      Read state file from disk(0 or 1)
  --qps QPS   The number of simultaneous DNS requests
  --dump      Write resolv dump to disk(0 or 1)
  --outfile   Write output prefix list to disk(0 or 1)
```

* target - префиксы какой длины мы хотим видеть на выходе(по дефолту /24)
* write - писать стейт-файл на основе etag/size 
* read - сверять ли со стейт-файлом содержимое на github
* qps - число параллельных запросов к DNS-серверу
* dump - писать ли дам того ресолва на диск
* outfile - файл куда писать итоговый список префиксов