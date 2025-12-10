## Basic operators

Milvus supports several basic operators for filtering data:

- **Comparison Operators** : `==` , `!=` , `>` , `<` , `>=` , and `<=` allow filtering based on numeric or text fields.
- **Range Filters** : `IN` and `LIKE` help match specific value ranges or sets.
- **Arithmetic Operators** : `+` , `-` , `*` , `/` , `%` , and `**` are used for calculations involving numeric fields.
- **Logical Operators** : `AND` , `OR` , and `NOT` combine multiple conditions into complex expressions.
- **IS NULL and IS NOT NULL Operators** : The `IS NULL` and `IS NOT NULL` operators are used to filter fields based on whether they contain a null value (absence of data). For details, refer to [Basic Operators](\docs\basic-operators.md#IS-NULL-and-IS-NOT-NULL-Operators) .

### Example: Filtering by Color

To find entities with primary colors (red, green, or blue) in a scalar field `color` , use the following filter expression:

```
filter = 'color in ["red", "green", "blue"]'
```

### Example

To find individuals over the age of 25 living in either "北京" (Beijing) or "上海" (Shanghai), use the following template expression:

```
filter = "age > 25 AND city IN ['北京', '上海']"
```