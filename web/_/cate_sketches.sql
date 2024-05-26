INSERT INTO `item` (`id`, `cate`, `owner`, `name`, `price`, `disc`, `photos`, `attributes`, `desc`, `quant`, `color`, `slug`, `sku`, `location`, `status`, `deleted`, `created`, `updated`) VALUES
(1, 77, NULL, 'Classic', 425000.00, NULL, '["prod.png"]', '["8kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(2, 77, NULL, 'BisTN', 395000.00, NULL, '["prod1.png"]', '["6kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(3, 77, NULL, 'Three KVA', 180000.00, NULL, '["prod7.png"]', '["3kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(4, 77, NULL, 'Edon, Ed-IG-1500', 295000.00, NULL, '["prod6.png"]', '["5kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(5, 77, NULL, 'Silent', 537000.00, NULL, '["prod5.png"]', '["10kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(6, 77, NULL, 'Generac', 820000.00, NULL, '["prod4.png"]', '["20kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(7, 77, NULL, '12Kva', 615000.00, NULL, '["prod3.png"]', '["12kva"]', 'Sound proof and battery generator. It do\"esnt use fuel or diesel. Uses battery and there\"s an inbuild alternator that charges itself. Works for 		20hrs. Comes with 2yrs warranty.', 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);



->super category (lev-0)
INSERT INTO `cate`(`name`, `parent`) 
VALUES ('Services','0'), ('Free Stuffs', '0'), ('Property','0'), ('Apparrel','0'), ('Office Supplies','0'), ('Home & Garden','0'), ('Entertainment','0'), ('
Fashion & Accessories','0'), ('Family','0'), ('Electronics','0'), ('Hobbies','0'), ('Classifieds','0'), ('Vehicles','0');

->main category (lev-1)
INSERT INTO `cate`(`name`, `lev`, `parent`) 
VALUES ('Cleaning','1', '1'), ('IT', '1', '1'), ('Automotive','1', '1'), ('Building & Trading','1',  '1'), ('Childcare & Education','1', '1'), ('Classes & Courses','1', '1'), ('Recruitment','1', '1'), ('
Fashion & Accessories','1', '1'), ('Family','1', '1'), ('Electronics','1', '1'), ('Hobbies','1', '1'), ('Classifieds','1', '1'), ('Vehicles','1', '1');

->sub category (lev-2) (services)
INSERT INTO `cate`(`name`, `lev`, `parent`) 
VALUES ('Cleaning','1', '1'), ('IT', '1','1'), ('Automotive','1','1'), ('Building & Trading','1','1'), ('Childcare & Education','1', '1'), ('Classes & Courses','1', '1'), ('Recruitment','1','1'),('Fitness & Personal Trading','1', '1'), ('Health & Beauty','1', '1'), ('Tax & Financial','1', '1'), ('Legal','1', '1'), ('Landscaping & Gardening','1', '1'), ('Manufacturing','1', '1'), ('Weddings & Venues','1', '1'), ('Printing','1', '1'), ('Travel & Tours','1', '1'), ('Rental','1', '1'), ('Repairs','1', '1');

->mini category (lev-3)
INSERT INTO `cate`(`name`, `lev`, `parent`) 
VALUES ('Cleaning','1', '2'), ('IT', '1', '2'), ('Property','1', '2'), ('Apparrel','1',  '2'), ('Office Supplies','1', '2'), ('Home & Garden','1', '2'), ('Entertainment','1', '2'), ('
Fashion & Accessories','1', '2'), ('Family','1', '2'), ('Electronics','1', '2'), ('Hobbies','1', '2'), ('Classifieds','1', '2'), ('Vehicles','1', '2');



->sub category (lev-2) (Home & Gardens)
INSERT INTO `cate`(`name`, `lev`, `parent`) 
VALUES ('Tools','1', '6'), ('Furniture', '1','6'), ('Household','1','6'), ('Garden','1','6'), 
('Appliances','1', '6');

//------------//
->sub category (lev-2) (entertainment)
INSERT INTO `cate`(`name`, `parent`, `lev`) 
VALUES ('Video games','7', '1'), ('Books', '7','1'), ('Movies & Music','7','1');

//------------//
->sub category (lev-2) (Fashion)
INSERT INTO `cate`(`name`, `parent`, `lev`) 
VALUES ('Bags & Luggage','8', '1'), ('Women"s clothing & Shoes', '8','1'), ('Men"s clothing & Shoes','8','1'),
('Jewelry & Accessories', '8', '1');
